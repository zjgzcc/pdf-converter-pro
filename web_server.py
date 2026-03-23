#!/usr/bin/env python3
"""
PDF Converter Pro - Web 服务器后端
🦎 影诺办 · 2026-03-19

功能：
1. PDF 转 WORD（可编辑文字，保持格式布局）
2. OCR 识别（扫描版转可搜索 PDF）
3. 去水印处理
4. 批量处理支持
"""

import os
import sys
import json
import time
import shutil
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import threading
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入核心模块
sys.path.insert(0, str(Path(__file__).parent))
# 🚀 优化：使用新版 OCR 模块（支持并行处理 + 表格优化）
from core.ocr_v2 import OCREngine, OCREngineType, OCRConfig, batch_ocr_parallel
from core.converter import PDF2WordConverter, ConvertMethod
from core.watermark import WatermarkRemover
from core.postprocess import rebuild_text_layer
from core.rapid_ocr import rapid_ocr_pdf

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# 全局状态
processing_status = {
    'is_processing': False,
    'progress': 0,
    'message': '就绪',
    'current_file': '',
    'total_files': 0,
    'processed_files': 0,
    'success_count': 0,
    'fail_count': 0,
    'logs': []
}

# 临时目录
TEMP_DIR = Path(tempfile.gettempdir()) / 'pdf_converter_pro'
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# 输出目录（临时目录，处理完通过浏览器下载）
OUTPUT_DIR = TEMP_DIR / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def log_message(message: str, level: str = 'info'):
    """添加日志"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'time': timestamp,
        'message': message,
        'level': level
    }
    processing_status['logs'].append(log_entry)
    logger.info(f"[{level.upper()}] {message}")


def process_file(
    input_path: Path,
    output_dir: Path,
    options: Dict[str, Any],
    file_index: int,
    total_files: int
) -> bool:
    """处理单个文件"""
    try:
        filename = input_path.name
        log_message(f"📄 开始处理：{filename}", 'info')
        
        # 更新进度
        processing_status['current_file'] = filename
        processing_status['progress'] = int((file_index / total_files) * 100)
        
        current_file = input_path
        temp_files = []
        
        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 步骤 1: 去水印（如果启用）
        if options.get('watermark', False):
            log_message(f"🧹 {filename}: 去除水印中...", 'info')
            processing_status['message'] = f'去水印：{filename}'
            
            try:
                remover = WatermarkRemover(method='auto')
                
                if current_file.suffix.lower() == '.pdf':
                    # PDF 去水印：先转图片，去水印后再合并
                    import fitz
                    temp_dir = TEMP_DIR / f'watermark_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    temp_files.append(temp_dir)
                    
                    doc = fitz.open(str(current_file))
                    img_paths = []
                    
                    for page_num, page in enumerate(doc):
                        mat = fitz.Matrix(2.0, 2.0)
                        pix = page.get_pixmap(matrix=mat)
                        img_path = temp_dir / f'page_{page_num}.png'
                        pix.save(str(img_path))
                        img_paths.append(img_path)
                        
                        # 去水印
                        clean_path = temp_dir / f'clean_{page_num}.png'
                        remover.remove(img_path, clean_path)
                    
                    doc.close()
                    
                    # 合并回 PDF（简化处理，使用 img2pdf）
                    import img2pdf
                    watermarked_pdf = output_dir / f'nowatermark_{current_file.name}'
                    temp_files.append(watermarked_pdf)
                    
                    with open(watermarked_pdf, 'wb') as f:
                        f.write(img2pdf.convert([str(p) for p in img_paths if p.name.startswith('clean_')]))
                    
                    current_file = watermarked_pdf
                    log_message(f"🧹 {filename}: 去水印完成", 'success')
                else:
                    # 图片直接去水印
                    clean_path = output_dir / f'clean_{current_file.name}'
                    remover.remove(current_file, clean_path)
                    temp_files.append(clean_path)
                    current_file = clean_path
                    log_message(f"🧹 {filename}: 去水印完成", 'success')
                    
            except Exception as e:
                log_message(f"🧹 {filename}: 去水印失败 - {str(e)}", 'error')
                processing_status['fail_count'] += 1
                return False
        
        # 步骤 2: OCR 识别（如果启用）
        if options.get('ocr', False):
            log_message(f"🔍 {filename}: AI OCR 识别中（RapidOCR）...", 'info')
            processing_status['message'] = f'AI OCR 识别：{filename}'
            
            try:
                output_pdf = output_dir / f'searchable_{current_file.stem}.pdf'
                
                # 🚀 优先使用 RapidOCR（AI 引擎，精度远超 Tesseract）
                result = rapid_ocr_pdf(current_file, output_pdf, dpi=200)
                
                if result["success"]:
                    current_file = output_pdf
                    temp_files.append(output_pdf)
                    log_message(f"🔍 {filename}: AI OCR 完成（{result['pages']}页，{result['time']:.1f}秒）", 'success')
                else:
                    log_message(f"🔍 {filename}: RapidOCR 失败，回退 Tesseract - {result['error']}", 'warning')
                    # 回退到 Tesseract
                    ocr_engine = options.get('ocr_engine', 'ocrmypdf')
                    engine_type = OCREngineType(ocr_engine)
                    config = OCRConfig(
                        language='chi_sim+eng',
                        dpi=450,
                        enable_memory_optimization=True,
                        enhance_tables=False,
                    )
                    engine = OCREngine(engine_type=engine_type, config=config, preload_models=True)
                    ocr_result = engine.convert_to_searchable_pdf(current_file, output_pdf)
                    if ocr_result.success:
                        current_file = output_pdf
                        temp_files.append(output_pdf)
                        log_message(f"🔍 {filename}: Tesseract OCR 完成（{ocr_result.pages_processed}页）", 'success')
                    else:
                        log_message(f"🔍 {filename}: OCR 失败 - {ocr_result.error_message}", 'error')
                    
            except Exception as e:
                log_message(f"🔍 {filename}: OCR 失败 - {str(e)}", 'error')
                processing_status['fail_count'] += 1
                return False
        
        # 步骤 3: WORD 转换（如果启用）
        if options.get('word', False):
            log_message(f"📝 {filename}: 转换为 WORD...", 'info')
            processing_status['message'] = f'WORD 转换：{filename}'
            
            try:
                word_method = options.get('word_method', 'pdf2docx')
                convert_method = ConvertMethod(word_method)
                
                output_docx = output_dir / f'{current_file.stem}.docx'
                
                converter = PDF2WordConverter(
                    method=convert_method,
                    preserve_format=True
                )
                
                # 确保输入是 PDF
                if current_file.suffix.lower() != '.pdf':
                    log_message(f"📝 {filename}: 需要先转为 PDF", 'warning')
                    # 这里可以添加图片转 PDF 的逻辑
                    processing_status['fail_count'] += 1
                    return False
                
                success = converter.convert(current_file, output_docx)
                
                if success and output_docx.exists() and output_docx.stat().st_size > 0:
                    log_message(f"📝 {filename}: WORD 转换完成（可编辑文字）", 'success')
                else:
                    log_message(f"📝 {filename}: WORD 转换失败 - 文件不存在或为空", 'error')
                    processing_status['fail_count'] += 1
                    return False
                    
            except Exception as e:
                log_message(f"📝 {filename}: WORD 转换失败 - {str(e)}", 'error')
                traceback.print_exc()
                processing_status['fail_count'] += 1
                return False
        
        # 处理成功
        processing_status['success_count'] += 1
        log_message(f"✅ {filename}: 处理完成", 'success')
        return True
        
    except Exception as e:
        log_message(f"❌ {filename}: 处理异常 - {str(e)}", 'error')
        traceback.print_exc()
        processing_status['fail_count'] += 1
        return False
    finally:
        # 清理临时文件
        processing_status['processed_files'] += 1
        processing_status['progress'] = int((processing_status['processed_files'] / total_files) * 100)


@app.route('/')
def index():
    """首页"""
    return send_from_directory('.', 'web_ui.html')


@app.route('/api/status')
def get_status():
    """获取处理状态"""
    return jsonify({
        'is_processing': processing_status['is_processing'],
        'progress': processing_status['progress'],
        'message': processing_status['message'],
        'current_file': processing_status['current_file'],
        'total_files': processing_status['total_files'],
        'processed_files': processing_status['processed_files'],
        'success_count': processing_status['success_count'],
        'fail_count': processing_status['fail_count'],
        'logs': processing_status['logs'][-50:]  # 返回最近 50 条日志
    })


@app.route('/api/test', methods=['POST'])
def test_api():
    """测试 API"""
    try:
        data = request.form.to_dict()
        files = request.files.getlist('files')
        return jsonify({
            'success': True,
            'message': 'API 测试成功',
            'received_files': len(files),
            'received_data': data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/api/process', methods=['POST', 'OPTIONS'])
def process_files():
    """处理文件"""
    if request.method == 'OPTIONS':
        return '', 204
    
    if processing_status['is_processing']:
        return jsonify({'error': '已有任务在处理中'}), 400
    
    try:
        # 获取请求数据
        data = request.form.to_dict()
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({'error': '请选择文件'}), 400
        
        # 解析选项
        options = {
            'watermark': data.get('watermark') == 'true',
            'ocr': data.get('ocr') == 'true',
            'word': data.get('word') == 'true',
            'ocr_engine': data.get('ocr_engine', 'ocrmypdf'),
            'word_method': data.get('word_method', 'pdf2docx'),
            'output_dir': str(OUTPUT_DIR)
        }
        
        # 验证至少选择一个功能
        if not any([options['watermark'], options['ocr'], options['word']]):
            return jsonify({'error': '请至少选择一个处理功能'}), 400
        
        # 输出目录固定为临时目录
        output_dir = OUTPUT_DIR
        # 每次处理前清空旧文件
        for old_file in output_dir.iterdir():
            if old_file.is_file():
                old_file.unlink()
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 重置状态
        processing_status['is_processing'] = True
        processing_status['progress'] = 0
        processing_status['message'] = '准备中...'
        processing_status['total_files'] = len(files)
        processing_status['processed_files'] = 0
        processing_status['success_count'] = 0
        processing_status['fail_count'] = 0
        processing_status['logs'] = []
        
        log_message('🚀 开始处理...', 'info')
        log_message(f'📊 文件数：{len(files)}', 'info')
        log_message(f'📁 输出目录：{output_dir}', 'info')
        log_message(f'⚙️ 选项：OCR ({options["ocr_engine"]}) + WORD ({options["word_method"]})', 'info')
        
        # 使用 print 直接输出调试信息（确保能看到）
        import sys
        sys.stdout.flush()
        print(f"[DEBUG] Files count: {len(files)}", flush=True)
        print(f"[DEBUG] Options: {options}", flush=True)
        
        try:
            # 先保存所有上传的文件到临时目录
            saved_files = []
            print(f"[DEBUG] Starting to save {len(files)} files...", flush=True)
            log_message(f"🔧 开始保存 {len(files)} 个文件...", 'info')
            for file in files:
                safe_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                input_path = TEMP_DIR / safe_filename
                print(f"[DEBUG] Saving file: {file.filename} -> {input_path}", flush=True)
                log_message(f"🔧 保存文件：{file.filename} -> {input_path}", 'info')
                file.save(str(input_path))
                saved_files.append(input_path)
                print(f"[DEBUG] File saved: {input_path}", flush=True)
                log_message(f"✅ 文件已保存：{input_path}", 'info')
            
            print(f"[DEBUG] Files saved, count: {len(saved_files)}", flush=True)
            log_message(f"🔧 准备启动后台线程，文件数：{len(saved_files)}", 'info')
        except Exception as e:
            print(f"[DEBUG] File save error: {str(e)}", flush=True)
            log_message(f"❌ 文件保存失败：{str(e)}", 'error')
            traceback.print_exc()
            raise
        
        # 🚀 优化：并行处理函数
        def process_in_background():
            log_message("🔧 后台线程已启动", 'info')
            try:
                # 🚀 优化：仅 OCR 功能启用并行处理
                if options.get('ocr', False) and not options.get('watermark', False) and not options.get('word', False):
                    # 纯 OCR 处理：使用并行处理
                    log_message(f"🚀 启用并行 OCR 处理：{len(saved_files)} 个文件", 'info')
                    
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    import gc
                    
                    max_workers = 2  # 同时处理 2 个文件
                    success_count = 0
                    fail_count = 0
                    
                    def process_single_ocr(input_path: Path, idx: int) -> bool:
                        """处理单个 OCR 任务"""
                        try:
                            log_message(f"🔍 [线程 {idx+1}/{len(saved_files)}] AI OCR 开始：{input_path.name}", 'info')
                            
                            processing_status['current_file'] = input_path.name
                            processing_status['progress'] = int((idx / len(saved_files)) * 100)
                            
                            output_pdf = output_dir / f'searchable_{input_path.stem}.pdf'
                            
                            # 🚀 优先用 RapidOCR
                            result = rapid_ocr_pdf(input_path, output_pdf, dpi=200)
                            
                            if result["success"]:
                                log_message(f"✅ [线程 {idx+1}] {input_path.name}: AI OCR 完成（{result['pages']}页，{result['time']:.1f}秒）", 'success')
                                processing_status['success_count'] += 1
                                return True
                            else:
                                log_message(f"❌ [线程 {idx+1}] {input_path.name}: OCR 失败 - {result['error']}", 'error')
                                processing_status['fail_count'] += 1
                                return False
                                
                        except Exception as e:
                            log_message(f"❌ [线程 {idx+1}] {input_path.name}: 异常 - {str(e)}", 'error')
                            processing_status['fail_count'] += 1
                            return False
                        finally:
                            processing_status['processed_files'] += 1
                            processing_status['progress'] = int((processing_status['processed_files'] / len(saved_files)) * 100)
                            gc.collect()
                    
                    # 🚀 并行处理
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = {
                            executor.submit(process_single_ocr, input_path, idx): input_path
                            for idx, input_path in enumerate(saved_files)
                        }
                        
                        for future in as_completed(futures):
                            try:
                                future.result()
                            except Exception as e:
                                log_message(f"❌ 线程异常：{str(e)}", 'error')
                    
                    log_message(f"🎉 并行处理完成！成功：{processing_status['success_count']}, 失败：{processing_status['fail_count']}", 'success')
                    
                else:
                    # 传统串行处理（去水印/WORD 转换需要顺序执行）
                    log_message(f"📋 使用串行处理：{len(saved_files)} 个文件", 'info')
                    for idx, input_path in enumerate(saved_files):
                        log_message(f"🔧 处理第 {idx+1} 个文件：{input_path}", 'info')
                        process_file(input_path, output_dir, options, idx, len(saved_files))
                    
                    log_message("🔧 所有文件处理完成", 'info')
                    
            except Exception as e:
                log_message(f"❌ 后台线程异常：{str(e)}", 'error')
                import traceback
                log_message(traceback.format_exc(), 'error')
            finally:
                processing_status['is_processing'] = False
                processing_status['message'] = '处理完成'
                log_message(f'🎉 全部完成！输出目录：{output_dir}', 'success')
        
        log_message("🔧 启动后台线程...", 'info')
        
        # 后台线程处理（不使用 daemon，让线程自然完成）
        thread = threading.Thread(target=process_in_background, daemon=False)
        thread.start()
        log_message("🔧 后台线程已启动", 'info')
        
        # 等待一小段时间确保线程开始执行
        time.sleep(0.1)
        
        return jsonify({
            'success': True,
            'message': f'开始处理 {len(files)} 个文件',
            'output_dir': str(output_dir)
        })
        
    except Exception as e:
        processing_status['is_processing'] = False
        log_message(f'❌ 处理异常：{str(e)}', 'error')
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/stop', methods=['POST'])
def stop_processing():
    """停止处理"""
    processing_status['is_processing'] = False
    processing_status['message'] = '已停止'
    log_message('⏹️ 用户停止处理', 'warning')
    return jsonify({'success': True})


@app.route('/api/outputs')
def list_outputs():
    """列出输出目录中的文件"""
    try:
        output_dir = OUTPUT_DIR
        if not output_dir.exists():
            return jsonify({'files': []})
        
        files = []
        for f in output_dir.iterdir():
            if f.is_file():
                files.append({
                    'name': f.name,
                    'size': f.stat().st_size,
                    'modified': datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                    'download_url': f'/api/download/{f.name}'
                })
        
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """下载文件"""
    try:
        # 安全检查：防止路径穿越
        safe_name = Path(filename).name
        file_path = OUTPUT_DIR / safe_name
        if not file_path.exists() or not file_path.is_file():
            return jsonify({'error': '文件不存在'}), 404
        
        return send_file(str(file_path), as_attachment=True, download_name=safe_name)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("PDF Converter Pro - Web Server")
    print("=" * 60)
    print(f"Temp Dir: {TEMP_DIR}")
    print(f"Output Dir: {OUTPUT_DIR}")
    print("URL: http://localhost:5000")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

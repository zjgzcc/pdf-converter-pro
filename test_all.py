#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Converter Pro - Comprehensive Unit Tests
"""

import sys
import os
import time
import requests
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul')
    sys.stdout.reconfigure(encoding='utf-8')

# Add project path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("PDF Converter Pro - Comprehensive Unit Tests")
print("=" * 60)

# Test 1: Core Module Import Tests
print("\n[Test 1] Core Module Import Tests")
print("-" * 60)

try:
    from core.ocr import OCREngine, OCREngineType, OCRConfig
    print("[PASS] OCR module imported successfully")
except Exception as e:
    print(f"[FAIL] OCR module import failed: {e}")

try:
    from core.converter import PDF2WordConverter, ConvertMethod
    print("[PASS] Converter module imported successfully")
except Exception as e:
    print(f"[FAIL] Converter module import failed: {e}")

try:
    from core.watermark import WatermarkRemover
    print("[PASS] Watermark module imported successfully")
except Exception as e:
    print(f"[FAIL] Watermark module import failed: {e}")

try:
    from core.pipeline import ProcessingPipeline, create_pipeline
    print("[PASS] Pipeline module imported successfully")
except Exception as e:
    print(f"[FAIL] Pipeline module import failed: {e}")

# Test 2: Web API Connectivity Tests
print("\n[Test 2] Web API Connectivity Tests")
print("-" * 60)

BASE_URL = "http://localhost:5000"

try:
    response = requests.get(f"{BASE_URL}/", timeout=5)
    if response.status_code == 200:
        print(f"[PASS] Homepage accessible (status: {response.status_code})")
    else:
        print(f"[FAIL] Homepage returned status: {response.status_code}")
except Exception as e:
    print(f"[FAIL] Homepage access error: {e}")

try:
    response = requests.get(f"{BASE_URL}/api/status", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"[PASS] Status API working (is_processing: {data.get('is_processing')})")
    else:
        print(f"[FAIL] Status API returned status: {response.status_code}")
except Exception as e:
    print(f"[FAIL] Status API error: {e}")

try:
    response = requests.post(f"{BASE_URL}/api/test", data={'test': 'value'}, timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"[PASS] Test API working: {data.get('message')}")
    else:
        print(f"[FAIL] Test API returned status: {response.status_code}")
except Exception as e:
    print(f"[FAIL] Test API error: {e}")

# Test 3: OCR Engine Availability
print("\n[Test 3] OCR Engine Availability Tests")
print("-" * 60)

try:
    from core.ocr import OCREngine, OCREngineType
    
    for engine_type in [OCREngineType.OCRMYDF, OCREngineType.TESSERACT]:
        try:
            engine = OCREngine(engine_type=engine_type)
            available = engine.is_engine_available()
            status = "AVAILABLE" if available else "NOT AVAILABLE"
            print(f"   {engine_type.value}: {status}")
        except Exception as e:
            print(f"   {engine_type.value}: ERROR - {e}")
            
except Exception as e:
    print(f"[FAIL] OCR engine test error: {e}")

# Test 4: Converter Module Tests
print("\n[Test 4] Converter Module Tests")
print("-" * 60)

try:
    from core.converter import PDF2WordConverter, ConvertMethod
    
    for method in [ConvertMethod.PDF2DOCX]:
        try:
            converter = PDF2WordConverter(method=method)
            print(f"   {method.value}: Initialized successfully")
        except Exception as e:
            print(f"   {method.value}: ERROR - {e}")
            
except Exception as e:
    print(f"[FAIL] Converter test error: {e}")

# Test 5: File Upload Test (if test file exists)
print("\n[Test 5] File Upload Test")
print("-" * 60)

test_pdf = Path(__file__).parent / "examples" / "test.pdf"
if not test_pdf.exists():
    test_pdf = Path(__file__).parent / "test_sample.pdf"
    if not test_pdf.exists():
        # Create test PDF
        try:
            import fitz
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), "Test PDF", fontsize=12)
            doc.save(str(test_pdf))
            doc.close()
            print(f"   Created test PDF: {test_pdf}")
        except Exception as e:
            print(f"   Could not create test PDF: {e}")
            test_pdf = None

if test_pdf and test_pdf.exists():
    try:
        with open(test_pdf, 'rb') as f:
            files = {'files': ('test.pdf', f, 'application/pdf')}
            data = {
                'watermark': 'false',
                'ocr': 'true',
                'word': 'false',
                'ocr_engine': 'ocrmypdf',
                'word_method': 'pdf2docx',
                'output_dir': str(Path.home() / 'Desktop' / 'PDF_Converter_Output')
            }
            
            print(f"   Uploading: {test_pdf.name}")
            response = requests.post(f"{BASE_URL}/api/process", files=files, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                print(f"[PASS] Upload successful: {result.get('message')}")
                print(f"   Output dir: {result.get('output_dir')}")
                
                # Poll status
                print("   Waiting for processing...")
                for i in range(30):
                    time.sleep(1)
                    status_response = requests.get(f"{BASE_URL}/api/status", timeout=5)
                    status = status_response.json()
                    
                    if not status.get('is_processing', True):
                        print(f"[PASS] Processing complete! Success: {status.get('success_count')}, Failed: {status.get('fail_count')}")
                        if status.get('logs'):
                            print("   Last logs:")
                            for log in status['logs'][-5:]:
                                print(f"      [{log['level']}] {log['message']}")
                        break
                    else:
                        print(f"   Progress: {status.get('progress')}% - {status.get('message')}")
                else:
                    print("   WARNING: Processing timeout")
            else:
                print(f"[FAIL] Upload failed (status: {response.status_code})")
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"[FAIL] Upload error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   SKIP: No test file available")

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)
print("All executable tests completed.")
print("Check above output for detailed results.")
print("=" * 60)

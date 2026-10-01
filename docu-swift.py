import os
import zipfile
import pymupdf
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from pdf2docx import Converter
from pypdf import PdfReader, PdfWriter
import img2pdf
from docx2pdf import convert

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "DocuSwift All-in-One Backend is running!"})

@app.route('/convert-pdf-to-word', methods=['POST'])
def convert_pdf_to_word():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file and file.filename.lower().endswith('.pdf'):
        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        docx_filename = os.path.splitext(file.filename)[0] + '.docx'
        docx_path = os.path.join(OUTPUT_FOLDER, docx_filename)
        file.save(pdf_path)
        try:
            cv = Converter(pdf_path)
            cv.convert(docx_path, start=0, end=None)
            cv.close()
            return send_file(docx_path, as_attachment=True, download_name=docx_filename)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    return jsonify({"error": "Invalid file format"}), 400

@app.route('/word-to-pdf', methods=['POST'])
def word_to_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file and (file.filename.lower().endswith('.doc') or file.filename.lower().endswith('.docx')):
        doc_path = os.path.join(UPLOAD_FOLDER, file.filename)
        pdf_filename = os.path.splitext(file.filename)[0] + '.pdf'
        pdf_path = os.path.join(OUTPUT_FOLDER, pdf_filename)
        file.save(doc_path)
        try:
            convert(doc_path, pdf_path)
            return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if os.path.exists(doc_path):
                os.remove(doc_path)
    return jsonify({"error": "Invalid file format"}), 400

@app.route('/pdf-to-images', methods=['POST'])
def pdf_to_images():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file and file.filename.lower().endswith('.pdf'):
        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(pdf_path)
        images_paths = []
        try:
            doc = pymupdf.open(pdf_path)
            base_name = os.path.splitext(file.filename)[0]
            for i, page in enumerate(doc):
                pix = page.get_pixmap()
                img_name = f"{base_name}_page_{i+1}.png"
                img_path = os.path.join(OUTPUT_FOLDER, img_name)
                pix.save(img_path)
                images_paths.append(img_path)
            
            zip_filename = f"{base_name}_images.zip"
            zip_path = os.path.join(OUTPUT_FOLDER, zip_filename)
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for img in images_paths:
                    zipf.write(img, os.path.basename(img))
            
            return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            for img in images_paths:
                if os.path.exists(img):
                    try:
                        os.remove(img)
                    except:
                        pass
    return jsonify({"error": "Invalid file format"}), 400

@app.route('/image-to-pdf', methods=['POST'])
def image_to_pdf():
    if 'files' not in request.files:
        return jsonify({"error": "No images uploaded"}), 400
    files = request.files.getlist('files')
    saved_paths = []
    try:
        for file in files:
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            saved_paths.append(path)
        output_filename = "converted_images.pdf"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(saved_paths))
        return send_file(output_path, as_attachment=True, download_name=output_filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)

@app.route('/compress-pdf', methods=['POST'])
def compress_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file and file.filename.lower().endswith('.pdf'):
        pdf_path = os.path.join(UPLOAD_FOLDER, file.filename)
        output_filename = "compressed_" + file.filename
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        file.save(pdf_path)
        try:
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            with open(output_path, "wb") as f:
                writer.write(f)
            return send_file(output_path, as_attachment=True, download_name=output_filename)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
    return jsonify({"error": "Invalid file format"}), 400

if __name__ == '__main__':
    print("Starting All-in-One backend server on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
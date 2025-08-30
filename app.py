import io

import pdfplumber
from flask import Flask, request, send_file, render_template_string
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

app = Flask(__name__)
pdfmetrics.registerFont(TTFont("Garamond", "./asset/fonts/Garamond.ttf"))
pdfmetrics.registerFont(TTFont("Garamond-Bold", "./asset/fonts/Garamonb.ttf"))


# Function to extract "Ship To" addresses only
def extract_ship_to_addresses(file_stream):
    ship_to_addresses = []
    with pdfplumber.open(file_stream) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines = text.split("\n")
                for i, line in enumerate(lines):
                    if line.strip().lower() == "ship to":
                        address_block = []
                        j = i + 1
                        while j < len(lines) and lines[j].strip():
                            if lines[j].strip().lower() == "ship from":
                                break
                            address_block.append(lines[j].strip())
                            j += 1
                        if address_block:
                            # print(address_block)
                            # Replace Ship To with Deliver To
                            ship_to_addresses.append("Deliver To\n" + "\n".join(address_block))
    return ship_to_addresses


UPLOAD_FORM = UPLOAD_FORM = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Upload PDF to Extract Ship To Addresses</title>

  <!-- Optional: nice font -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">

  <style>
    :root{
      --bg: #0f172a;          /* slate-900 */
      --card: #111827;        /* gray-900 */
      --muted: #9ca3af;       /* gray-400 */
      --text: #e5e7eb;        /* gray-200 */
      --accent: #6366f1;      /* indigo-500 */
      --accent-600: #5458ee;
      --ring: rgba(99,102,241,.35);
      --success: #22c55e;
      --border: #1f2937;      /* gray-800 */
    }

    @media (prefers-color-scheme: light){
      :root{
        --bg: #f8fafc;        /* slate-50 */
        --card: #ffffff;
        --muted: #6b7280;     /* gray-500 */
        --text: #0f172a;      /* slate-900 */
        --accent: #4f46e5;    /* indigo-600 */
        --accent-600: #4338ca;
        --ring: rgba(79,70,229,.25);
        --success: #16a34a;
        --border: #e5e7eb;    /* gray-200 */
      }
    }

    * { box-sizing: border-box; }
    html, body {
      height: 100%;
      margin: 0;
      font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Apple Color Emoji", "Segoe UI Emoji";
      color: var(--text);
      background:
        radial-gradient(1200px 600px at 10% -10%, rgba(99,102,241,.15), transparent 50%),
        radial-gradient(1000px 500px at 110% 10%, rgba(16,185,129,.12), transparent 50%),
        var(--bg);
    }

    .wrap {
      min-height: 100%;
      display: grid;
      place-items: center;
      padding: 32px 16px;
    }

    .card {
      width: 100%;
      max-width: 720px;
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 18px;
      box-shadow: 0 10px 30px rgba(0,0,0,.18);
      padding: 28px;
    }

    .title {
      margin: 0 0 6px 0;
      font-size: clamp(24px, 4vw, 34px);
      line-height: 1.1;
      letter-spacing: -.02em;
      font-weight: 700;
    }
    .sub {
      margin: 0 0 22px 0;
      color: var(--muted);
      font-size: 14px;
    }

    .dropzone {
      position: relative;
      border: 2px dashed var(--border);
      border-radius: 16px;
      padding: 28px;
      display: grid;
      gap: 12px;
      place-items: center;
      text-align: center;
      transition: border-color .2s, background-color .2s, transform .05s ease-in-out;
      background: rgba(255,255,255,.01);
    }
    .dropzone.dragover {
      border-color: var(--accent);
      background: rgba(99,102,241,.08);
      box-shadow: 0 0 0 6px var(--ring);
      transform: translateY(-1px);
    }

    .dz-icon {
      width: 56px; height: 56px;
      border-radius: 14px;
      display: grid; place-items: center;
      background: linear-gradient(145deg, rgba(99,102,241,.2), rgba(99,102,241,.08));
      border: 1px solid var(--border);
    }

    .file-label {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      border-radius: 12px;
      border: 1px solid var(--border);
      background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,0));
      cursor: pointer;
      transition: background .2s, border-color .2s, transform .05s;
      user-select: none;
    }
    .file-label:hover { border-color: var(--accent); }
    .file-label:active { transform: translateY(1px); }

    .hidden-input { display: none; }

    .file-name {
      font-size: 14px;
      color: var(--muted);
    }

    .actions {
      margin-top: 18px;
      display: flex;
      gap: 12px;
      justify-content: flex-end;
      flex-wrap: wrap;
    }

    .btn {
      appearance: none;
      border: 1px solid var(--border);
      background: var(--accent);
      color: white;
      font-weight: 600;
      padding: 12px 16px;
      border-radius: 12px;
      cursor: pointer;
      transition: transform .05s ease-in-out, background .2s, box-shadow .2s, opacity .2s;
      box-shadow: 0 6px 20px rgba(99,102,241,.35);
    }
    .btn:hover { background: var(--accent-600); }
    .btn:active { transform: translateY(1px); }
    .btn[disabled]{
      opacity: .6;
      cursor: not-allowed;
      box-shadow: none;
    }

    .hint { font-size: 12px; color: var(--muted); }

    .footer {
      margin-top: 18px;
      text-align: center;
      color: var(--muted);
      font-size: 12px;
    }
    .kbd {
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      border: 1px solid var(--border);
      padding: .2em .45em;
      border-radius: 6px;
      background: rgba(255,255,255,.05);
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1 class="title">Upload PDF to Extract Ship To Addresses</h1>
      <p class="sub">Drop your PDF here or choose a file. We’ll generate a neatly formatted, bordered label sheet.</p>

      <form method="post" action="/data" enctype="multipart/form-data" id="uploadForm">
        <div id="dropzone" class="dropzone" aria-label="PDF file dropzone">
          <div class="dz-icon" aria-hidden="true">
            <!-- Simple inline SVG icon -->
            <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.6">
              <rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" opacity=".6"></rect>
              <path d="M8 12h8M12 8v8" stroke="currentColor"></path>
            </svg>
          </div>

          <label for="fileInput" class="file-label">
            Choose PDF
            <span class="hint">or drag & drop</span>
          </label>
          <input id="fileInput" class="hidden-input" type="file" name="pdf" accept="application/pdf" required>

          <div id="fileName" class="file-name">No file selected</div>
          <div class="hint">Only PDF files are supported. Max 25MB is typical.</div>
          <div class="hint">Tip: You can also press <span class="kbd">Space</span> or <span class="kbd">Enter</span> on the button.</div>
        </div>

        <div class="actions">
          <button id="submitBtn" class="btn" type="submit" disabled>Upload &amp; Download Result</button>
        </div>
      </form>

      <div class="footer">Your file is processed locally by the server and not stored.</div>
    </div>
  </div>

  <script>
    (function(){
      const dropzone  = document.getElementById('dropzone');
      const input     = document.getElementById('fileInput');
      const submitBtn = document.getElementById('submitBtn');
      const fileName  = document.getElementById('fileName');

      function setFile(file){
        if(!file) return;
        input.files = new DataTransfer(); // create empty list
        const dt = new DataTransfer();
        dt.items.add(file);
        input.files = dt.files;
        fileName.textContent = file.name;
        submitBtn.disabled = false;
      }

      // Click to open file dialog
      dropzone.addEventListener('click', () => input.click());

      // Reflect manual selection
      input.addEventListener('change', () => {
        const f = input.files && input.files[0];
        if (f) {
          fileName.textContent = f.name;
          submitBtn.disabled = false;
        } else {
          fileName.textContent = "No file selected";
          submitBtn.disabled = true;
        }
      });

      // Drag & drop handlers
      ['dragenter', 'dragover'].forEach(evt =>
        dropzone.addEventListener(evt, (e) => {
          e.preventDefault(); e.stopPropagation();
          dropzone.classList.add('dragover');
        })
      );
      ['dragleave', 'drop'].forEach(evt =>
        dropzone.addEventListener(evt, (e) => {
          e.preventDefault(); e.stopPropagation();
          dropzone.classList.remove('dragover');
        })
      );
      dropzone.addEventListener('drop', (e) => {
        const file = e.dataTransfer.files && e.dataTransfer.files[0];
        if (!file) return;
        if (file.type !== 'application/pdf'){
          alert('Please drop a PDF file.');
          return;
        }
        setFile(file);
      });

      // Keyboard accessibility for the label area
      dropzone.tabIndex = 0;
      dropzone.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          input.click();
        }
      });
    })();
  </script>
</body>
</html>
"""



@app.route("/", methods=["GET"])
def index():
    return render_template_string(UPLOAD_FORM)


@app.route("/data", methods=["POST"])
def process_pdf():
    if "pdf" not in request.files:
        return "No file uploaded", 400
    file = request.files["pdf"]
    if file.filename == "":
        return "No selected file", 400

    addresses = extract_ship_to_addresses(file)

    buffer = io.BytesIO()
    PAGE_W, PAGE_H = 4 * inch, 9.5 * inch
    c = canvas.Canvas(buffer, pagesize=(PAGE_W, PAGE_H))

    # Fonts
    base_font = "Garamond-Bold"
    base_size = 14
    header_font = "Garamond-Bold"  # change to "Garamond-Bold" if you register a bold face
    header_size = 14

    # Layout
    margin_x = 8  # ~0.25"
    top_margin = 15
    bottom_margin = 10
    box_padding = 10
    line_height = base_size + 4  # 20 px for base lines
    gap_between = 20
    box_width = PAGE_W - 2 * margin_x

    from reportlab.lib import colors
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)

    y = PAGE_H - top_margin

    # Header above list (optional)
    c.setFont(base_font, base_size)
    c.drawString(margin_x, y, ">>>SA<<<")
    y -= 10

    for addr in addresses:
        lines = addr.split("\n")
        header_text = lines[0]  # "Deliver To"
        rest_lines = lines[1:]

        # Compute box height: header line + divider + remaining lines + paddings
        header_h = header_size + 6  # visual height of header row
        rest_h = len(rest_lines) * line_height
        box_height = box_padding + header_h + rest_h + box_padding  # +2 for thin divider clearance

        # New page if needed
        if y - box_height < bottom_margin:
            c.showPage()
            c.setStrokeColor(colors.black)
            c.setLineWidth(1)
            y = PAGE_H - top_margin

        # Outer rectangle
        box_x = margin_x
        box_y = y - box_height
        c.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)

        # --- Header ("Deliver To") ---
        c.setFont(header_font, header_size)
        header_baseline = y - box_padding - (header_size * 0.25)  # small visual tweak
        c.drawString(box_x + box_padding, header_baseline, header_text)

        # Divider line under header
        divider_y = y - header_h
        c.line(box_x, divider_y, box_x + box_width, divider_y)

        # --- Address lines ---
        c.setFont(base_font, base_size)
        text_y = divider_y - 16  # small gap below divider
        for line in rest_lines:
            c.drawString(box_x + box_padding, text_y, line)
            text_y -= line_height

        # Cursor below this box
        y = box_y - gap_between

    # Footer
    if y < bottom_margin:
        c.showPage()
        y = PAGE_H - top_margin
    c.setFont(base_font, base_size)
    c.drawString(margin_x, y, ">>>Finish<<<")

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="ship_to_addresses.pdf", mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True)

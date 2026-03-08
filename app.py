import streamlit as st
import segno
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
import io
import zipfile
import os
import numpy as np

st.set_page_config(page_title="QR Generator", page_icon="🔳")

st.title("BookMyShow QR Code Generator")

# -----------------------------
# Inputs
# -----------------------------

url = st.text_input("Enter URL")

qr_color = st.color_picker("QR Color", "#000000")
bg_color = st.color_picker("Background Color", "#FFFFFF")

border = st.slider("QR Border", 1, 10, 4)

qr_resolution = st.slider(
    "QR Resolution (px)",
    500,
    2000,
    1200,
    100
)

remove_logo = st.checkbox("Remove logo")

uploaded_logo = st.file_uploader(
    "Upload custom logo",
    type=["png","jpg","jpeg"]
)

# -----------------------------
# QR Rendering Functions
# -----------------------------

def draw_qr_matrix(matrix, resolution):

    size = len(matrix)

    module = resolution // size

    img = Image.new("RGBA", (size*module, size*module), bg_color)

    draw = ImageDraw.Draw(img)

    for y in range(size):
        for x in range(size):

            if matrix[y][x]:

                draw.rectangle(
                    (
                        x*module,
                        y*module,
                        (x+1)*module,
                        (y+1)*module
                    ),
                    fill=qr_color
                )

    return img


def draw_finder_pattern(draw, x, y, module):

    # outer frame
    draw.rectangle(
        (x, y, x+7*module, y+7*module),
        outline=qr_color,
        width=int(module)
    )

    # inner square
    draw.rectangle(
        (x+2*module, y+2*module, x+5*module, y+5*module),
        fill=qr_color
    )


# -----------------------------
# Generate QR
# -----------------------------

generate = st.button("Generate QR")

if generate and url:

    qr = segno.make(url, error='h')

    matrix = list(qr.matrix)

    img = draw_qr_matrix(matrix, qr_resolution)

    draw = ImageDraw.Draw(img)

    module = qr_resolution // len(matrix)

    # Finder positions
    draw_finder_pattern(draw, 0, 0, module)
    draw_finder_pattern(draw, (len(matrix)-7)*module, 0, module)
    draw_finder_pattern(draw, 0, (len(matrix)-7)*module, module)

    folder = "output"
    os.makedirs(folder, exist_ok=True)

    png_path = f"{folder}/qr.png"
    svg_path = f"{folder}/qr.svg"
    eps_path = f"{folder}/qr.eps"
    pdf_path = f"{folder}/qr.pdf"

    img.save(png_path)

    qr.save(svg_path)
    qr.save(eps_path)

    # -----------------------------
    # Logo
    # -----------------------------

    logo = None

    if not remove_logo:

        if uploaded_logo:
            logo = Image.open(uploaded_logo)
        else:
            logo = Image.open("default_logo.png")

    if logo:

        logo = logo.convert("RGBA")

        qr_w, qr_h = img.size

        logo_size = int(qr_w * 0.20)

        logo = logo.resize((logo_size,logo_size))

        pos = ((qr_w-logo_size)//2,(qr_h-logo_size)//2)

        # clear area behind logo
        bg_rgb = Image.new("RGB",(1,1),bg_color).getpixel((0,0))

        for x in range(pos[0], pos[0]+logo_size):
            for y in range(pos[1], pos[1]+logo_size):
                img.putpixel((x,y), (*bg_rgb,255))

        img.paste(logo,pos,logo)

        img.save(png_path)

    # -----------------------------
    # PDF exact size
    # -----------------------------

    width, height = img.size

    c = canvas.Canvas(pdf_path, pagesize=(width,height))
    c.drawImage(png_path,0,0,width,height)
    c.save()

    # -----------------------------
    # Preview
    # -----------------------------

    st.image(png_path)

    # -----------------------------
    # Individual downloads
    # -----------------------------

    col1,col2,col3,col4 = st.columns(4)

    with col1:
        with open(png_path,"rb") as f:
            st.download_button("PNG",f,"qr.png")

    with col2:
        with open(svg_path,"rb") as f:
            st.download_button("SVG",f,"qr.svg")

    with col3:
        with open(eps_path,"rb") as f:
            st.download_button("EPS",f,"qr.eps")

    with col4:
        with open(pdf_path,"rb") as f:
            st.download_button("PDF",f,"qr.pdf")

    # -----------------------------
    # ZIP
    # -----------------------------

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer,"a",zipfile.ZIP_DEFLATED) as z:

        z.write(png_path,"qr.png")
        z.write(svg_path,"qr.svg")
        z.write(eps_path,"qr.eps")
        z.write(pdf_path,"qr.pdf")

    zip_buffer.seek(0)

    st.download_button(
        "Download All (ZIP)",
        zip_buffer,
        file_name="qr_codes.zip"
    )

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    after_this_request,
)
from rembg import remove
import os

app = Flask(__name__)

# Configure uploads directory
app.config["UPLOAD_FOLDER"] = "uploads"
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

allowed_extensions = {"png", "jpg", "jpeg"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def remove_background(image_path):
    """
    Removes background from an image using Rembg and saves the processed image.

    Args:
        image_path: Path to the image file.

    Returns:
        Path to the processed image file with removed background, or None if error.
    """
    try:
        with open(image_path, "rb") as f:
            output = remove(f.read())
        base_filename = os.path.splitext(os.path.basename(image_path))[0]
        output_path = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{base_filename}_processed.png"
        )
        with open(output_path, "wb") as out:
            out.write(output)
        return output_path
    except Exception as e:
        print(f"Error removing background: {e}")
        return None


@app.route("/", methods=["GET", "POST"])
def upload_image():
    if request.method == "POST":
        # Check if the post request has the file part
        if "image" not in request.files:
            return redirect(request.url)
        image_file = request.files["image"]
        # If the user does not select a file, the browser submits an empty file without a filename.
        if image_file.filename == "":
            return redirect(request.url)
        if image_file and allowed_file(image_file.filename):
            image_path = os.path.join(app.config["UPLOAD_FOLDER"], image_file.filename)
            image_file.save(image_path)
            processed_path = remove_background(image_path)
            if processed_path:
                return render_template(
                    "result.html",
                    original_image=os.path.basename(image_path),
                    processed_image=os.path.basename(processed_path),
                )
            else:
                return redirect(url_for("upload_image", error="Error processing image"))
        else:
            return redirect(url_for("upload_image", error="Invalid file type"))

    return render_template("index.html")


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    @after_this_request
    def remove_file(response):
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        except Exception as e:
            print(f"Error deleting file: {e}")
        return response

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=os.environ.get('PORT', 5000))

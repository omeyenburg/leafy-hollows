use gl::types::*;
use image::DynamicImage;
use image::GenericImageView;

fn load_png(png_bytes: &[u8]) -> DynamicImage {
    // Load the PNG image from a file or a byte slice
    image::load_from_memory(png_bytes).expect("Failed to load image")
}

fn image_to_texture(image: &DynamicImage) -> GLuint {
    let mut texture_id = 0;
    let (width, height) = image.dimensions();
    let data = image.to_rgba8().into_raw();

    unsafe {
        gl::GenTextures(1, &mut texture_id);
        gl::BindTexture(gl::TEXTURE_2D, texture_id);
        gl::TexImage2D(
            gl::TEXTURE_2D,
            0,
            gl::RGBA as GLint,
            width as GLsizei,
            height as GLsizei,
            0,
            gl::RGBA,
            gl::UNSIGNED_BYTE,
            data.as_ptr() as *const GLvoid,
        );

        // Set texture parameters, e.g., filtering and wrapping options
        // ...
        gl::TexParameteri(gl::TEXTURE_2D, gl::TEXTURE_MIN_FILTER, gl::NEAREST as i32);
        gl::TexParameteri(gl::TEXTURE_2D, gl::TEXTURE_MAG_FILTER, gl::NEAREST as i32);

        gl::BindTexture(gl::TEXTURE_2D, 0);
    }

    texture_id
}

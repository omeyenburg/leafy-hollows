use crate::constants::*;
use gl::types::*;
use image::DynamicImage;
use image::GenericImageView;

pub struct Textures {
    tex_sprites: GLuint,
    tex_blocks: GLuint,
    tex_font: GLuint,
    tex_world: GLuint,
    tex_shadow: GLuint,
}

impl Textures {
    pub fn new() -> Self {
        let [tex_sprites, tex_blocks, tex_font, tex_world, tex_shadow] = {
            let mut textures: [gl::types::GLuint; 5] = [0; 5];
            unsafe {
                gl::GenBuffers(5, textures.as_mut_ptr());
            }
            textures
        };

        Self::image_to_texture(tex_sprites, IMAGE_SPRITES);

        unsafe {
            gl::BindTexture(gl::TEXTURE_2D, tex_sprites);
            gl::ActiveTexture(gl::TEXTURE0);
            gl::BindTexture(gl::TEXTURE_2D, 0);
        }

        Self {
            tex_sprites,
            tex_blocks,
            tex_font,
            tex_world,
            tex_shadow,
        }
    }

    fn load_image(bytes: &[u8]) -> DynamicImage {
        image::load_from_memory(bytes).unwrap()
    }

    fn image_to_texture(texture_id: GLuint, bytes: &[u8]) {
        let image = Self::load_image(bytes);
        let (width, height) = image.dimensions();
        let data: Vec<u8> = image.to_rgba8().into_raw();

        unsafe {
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

            let border_color = vec![0.0, 0.0, 0.0, 0.0];
            gl::TexParameteri(gl::TEXTURE_2D, gl::TEXTURE_MIN_FILTER, gl::NEAREST as i32);
            gl::TexParameteri(gl::TEXTURE_2D, gl::TEXTURE_MAG_FILTER, gl::NEAREST as i32);
            gl::TexParameteri(
                gl::TEXTURE_2D,
                gl::TEXTURE_WRAP_S,
                gl::CLAMP_TO_BORDER as i32,
            );
            gl::TexParameteri(
                gl::TEXTURE_2D,
                gl::TEXTURE_WRAP_T,
                gl::CLAMP_TO_BORDER as i32,
            );
            gl::TexParameteri(
                gl::TEXTURE_2D,
                gl::TEXTURE_WRAP_R,
                gl::CLAMP_TO_BORDER as i32,
            );
            gl::TexParameterfv(
                gl::TEXTURE_2D,
                gl::TEXTURE_BORDER_COLOR,
                border_color.as_ptr() as *const f32,
            );

            gl::BindTexture(gl::TEXTURE_2D, 0);
        }
    }
}


impl Drop for Textures {
    fn drop(&mut self) {
    }
}

use crate::constants::*;
use gl::types::*;
use gl::NUM_SAMPLE_COUNTS;
use image::DynamicImage;
use image::GenericImageView;

pub struct Textures {
    pub tex_sprites: GLuint,
    tex_blocks: GLuint,
    pub tex_font: GLuint,
    tex_world: GLuint,
    tex_shadow: GLuint,
}

impl Textures {
    pub fn new() -> Self {
        /*
        let [tex_sprites, tex_blocks, tex_font, tex_world, tex_shadow] = {
            let mut textures: [gl::types::GLuint; 5] = [0; 5];
            unsafe {
                gl::GenBuffers(5, textures.as_mut_ptr());
            }
            textures
        };*/
        let mut tex_sprites: gl::types::GLuint = 0;
        let mut tex_blocks: gl::types::GLuint = 0;
        let mut tex_font: gl::types::GLuint = 0;
        let mut tex_world: gl::types::GLuint = 0;
        let mut tex_shadow: gl::types::GLuint = 0;

        unsafe {
            // Sprites
            gl::GenTextures(1, &mut tex_sprites);
            gl::BindTexture(gl::TEXTURE_2D, tex_sprites);

            gl::ActiveTexture(gl::TEXTURE0);
            //gl::BindTexture(gl::TEXTURE_2D, tex_sprites);
            Self::image_to_texture(tex_sprites, SPRITES_IMAGE);

            // Blocks
            gl::GenTextures(1, &mut tex_blocks);
            gl::BindTexture(gl::TEXTURE_2D, tex_blocks);

            // Font
            gl::GenTextures(1, &mut tex_font);
            gl::BindTexture(gl::TEXTURE_2D, tex_font);

            gl::ActiveTexture(gl::TEXTURE1);
            //gl::BindTexture(gl::TEXTURE_2D, tex_font);
            Self::image_to_texture(tex_font, FONT_IMAGE);

            // World
            gl::GenTextures(1, &mut tex_world);
            gl::BindTexture(gl::TEXTURE_2D, tex_world);

            // Shadow
            gl::GenTextures(1, &mut tex_shadow);
            gl::BindTexture(gl::TEXTURE_2D, tex_shadow);
        }
        /*
        let mut tex_sprites: u32;
        let mut tex_blocks: u32;
        let mut tex_font: u32;
        let mut tex_world: u32;
        let mut tex_shadow: u32;
        unsafe {
            gl::GenTextures(1, tex_sprites.as_mut_ptr());
            gl::BindTexture(gl::TEXTURE_2D, tex_sprites);

            gl::GenTextures(1, *tex_blocks);
            gl::BindTexture(gl::TEXTURE_2D, tex_blocks);

            gl::GenTextures(1, &tex_font);
            gl::BindTexture(gl::TEXTURE_2D, tex_font);

            gl::GenTextures(1, &tex_world);
            gl::BindTexture(gl::TEXTURE_2D, tex_world);

            gl::GenTextures(1, &tex_shadow);
            gl::BindTexture(gl::TEXTURE_2D, tex_shadow);
        }*/



        println!(
            "Textures:\n- Sprites: {}\n- Blocks: {}\n- Font: {}",
            tex_sprites, tex_blocks, tex_font
        );

        unsafe {
            
            gl::BindTexture(gl::TEXTURE_2D, tex_sprites);
            
            
            gl::BindTexture(gl::TEXTURE_2D, tex_font);
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
    fn drop(&mut self) {}
}

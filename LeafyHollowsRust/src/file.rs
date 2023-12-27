use std::path::{Path, PathBuf};
use crate::constants;

extern crate directories;
use directories::ProjectDirs;


fn get_project_directory() -> ProjectDirs {
    if let Some(project_directory) = ProjectDirs::from("", "",  constants::PROJECT_DIRECTORY) {
        return project_directory;
    } else {
        panic!("Could not get project directory");
    }
}

pub fn get_config_directory() -> PathBuf {
    let dirs: ProjectDirs = get_project_directory();
    dirs.config_dir().to_path_buf()
}

pub fn get_data_directory() -> PathBuf {
    let dirs: ProjectDirs = get_project_directory();
    dirs.data_dir().to_path_buf()
}
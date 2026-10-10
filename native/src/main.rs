#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
mod backend;
use backend::{BackendProcess, spawn_backend};
use tauri::{Emitter, Manager};

fn main() {
    // Force the Blink accessibility tree so UI automation (pywinauto CUA
    // release gate) and screen readers see web content as UIA elements.
    // WebView2 honors this env var natively; Tauri v2 has no config key
    // for browser args, so the env var IS the mechanism. Must precede Builder.
    std::env::set_var(
        "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS",
        "--force-renderer-accessibility",
    );
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .manage(BackendProcess(std::sync::Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle().clone();
            if let Err(e) = spawn_backend(handle.clone(), app.state::<BackendProcess>().inner()) {
                eprintln!("Backend error: {e}");
                let _ = handle.emit("backend-status", format!("error: {e}"));
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error building tauri application")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(mut child) = app.state::<BackendProcess>().0.lock().unwrap().take() {
                    let _ = child.kill();
                    let _ = child.wait();
                }
            }
        });
}

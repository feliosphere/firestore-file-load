# 🚀 Project TODO List: Firebase CSV Uploader (v0.1.0)

This document tracks immediate development tasks and future features for the `firebase-data-uploader` project.

---

## 🎯 Phase 1: Refactoring & Infrastructure (Current Focus)

These are the tasks required to finalize the new layered architecture.

### ✅ Infrastructure Checklist

* [x] Create project files: `pyproject.toml`, `README.md`, `.gitignore`, `requirements.txt`.
* [x] Finalize the `firebase_uploader/__init__.py` file (use for convenient imports).
* [x] Finalize `pyproject.toml`

### 🛠️ Code Implementation

* [x] Define the `UploaderInterface` in `firebase_uploader/uploader_interface.py`.
* [x] Refactor and implement `FirestoreRepository` in `firebase_uploader/repository.py`, ensuring it adheres to `UploaderInterface`.
    * [x] Implement private `_connect_to_firestore()` within the class.
    * [x] Ensure `upload_document()` uses `self._db_client`.
* [x] Refactor and implement the core business logic in `firebase_uploader/service.py`.
    * [x] Implement the `get_fields()` data transformation logic.
    * [x] Implement `process_and_upload_csv()`, instantiating and using `FirestoreRepository`.
* [x] Refactor the CLI logic in `firebase_uploader/cli.py`.
    * [x] Implement `cli_entrypoint()`.
* [x] Create `firebase_uploader/__main__.py` to enable execution via `python -m firebase_uploader`.

### License
* [x] Add licencing file
* [x] Add copyrite comments to files. 

---

## 🧪 Phase 2: Testing and Core Feature Completion

Focus on ensuring the existing and new core functionality is stable.

* [ ] **Testing Setup:**
    * [ ] Install `pytest`.
    * [ ] Create a basic test file: `tests/test_core.py`.
    * [ ] Implement a **Mock Repository** to test `service.py` without actual Firebase calls.
* [ ] Update README.

---

## 🚴 Phase 3: Features
* [ ] **New Upload Mode:**
    * [ ] Implement the "document" mode logic in `process_and_upload_csv()` in `
* [ ] **New grouped fields feature**
    * [ ] Implement the "grouped fields" by CSV data naming conventions.
* [x] Implement flag for emulator vs cloud
* [x] **Field types Support** 
    * [x] First implementation on field type

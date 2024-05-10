import time
import zipfile
import os
import requests
from pydicom import dcmread
from pynetdicom import AE, AllStoragePresentationContexts, StoragePresentationContexts, ALL_TRANSFER_SYNTAXES
from pynetdicom.presentation import PresentationContext
from pydicom.errors import InvalidDicomError
from datetime import datetime
import logging
from pynetdicom.sop_class import (
  Verification,
)

LOGGER = logging.getLogger("flask_server")
ALLOWED_EXTENSIONS = {'dcm', 'zip'}

def allowed_file(filename):
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_metadata(collection, file_dcm, pathname):
  if collection == "patient":
    return {
      "patient_id": str(file_dcm.PatientID) if hasattr(file_dcm, 'PatientID') else None,
      "patient_name": str(file_dcm.PatientName) if hasattr(file_dcm, 'PatientName') else None,
    }
  elif collection == "study":
    return {
      "patient_id": str(file_dcm.PatientID) if hasattr(file_dcm, 'PatientID') else None,
      "study_id": str(file_dcm[0x0020, 0x0010].value) if [0x0020, 0x0010] in file_dcm else None,
      "study_instance_uid": str(file_dcm.StudyInstanceUID) if hasattr(file_dcm, 'StudyInstanceUID') else None,
      "study_date": str(file_dcm.StudyDate) if hasattr(file_dcm, 'StudyDate') else None,
      "study_time": str(file_dcm.StudyTime) if hasattr(file_dcm, 'StudyTime') else None,
      "study_description": str(file_dcm.StudyDescription) if hasattr(file_dcm, 'StudyDescription') else None,
      "accession_number": str(file_dcm.AccessionNumber) if hasattr(file_dcm, 'AccessionNumber') else None,
    }
  elif collection == "series":
    return {
      "patient_id": str(file_dcm.PatientID) if hasattr(file_dcm, 'PatientID') else None,
      "study_id": str(file_dcm[0x0020, 0x0010].value) if [0x0020, 0x0010] in file_dcm else None,
      "series_number": str(file_dcm.SeriesNumber) if hasattr(file_dcm, 'SeriesNumber') else None,
      "series_instance_uid": str(file_dcm.SeriesInstanceUID) if hasattr(file_dcm, 'SeriesInstanceUID') else None,
      "series_date": str(file_dcm.SeriesDate) if hasattr(file_dcm, 'SeriesDate') else None,
      "series_time": str(file_dcm.SeriesTime) if hasattr(file_dcm, 'SeriesTime') else None,
      "series_description": str(file_dcm.SeriesDescription) if hasattr(file_dcm, 'SeriesDescription') else None,
      "body_part_examined": str(file_dcm.BodyPartExamined) if hasattr(file_dcm, 'BodyPartExamined') else None,
      "modality": str(file_dcm.Modality) if hasattr(file_dcm, 'Modality') else None,
    }
  elif collection == "image":
    return {
      "patient_id": str(file_dcm.PatientID) if hasattr(file_dcm, 'PatientID') else None,
      "study_id": str(file_dcm[0x0020, 0x0010].value) if [0x0020, 0x0010] in file_dcm else None,
      "series_number": str(file_dcm.SeriesNumber) if hasattr(file_dcm, 'SeriesNumber') else None,
      "instance_number": str(file_dcm.InstanceNumber) if hasattr(file_dcm, 'InstanceNumber') else None,
      "sop_instance_uid": str(file_dcm.SOPInstanceUID) if hasattr(file_dcm, 'SOPInstanceUID') else None,
      # others
      "path": str(pathname),
    }
  else:
    return None

def dicom_written(pathname):
  try:
    file_dcm = dcmread(pathname, force=True)

    dcm_metadata_patient = generate_metadata("patient", file_dcm, pathname)
    dcm_metadata_study = generate_metadata("study", file_dcm, pathname)
    dcm_metadata_series = generate_metadata("series", file_dcm, pathname)
    dcm_metadata_image = generate_metadata("image", file_dcm, pathname)

    print(dcm_metadata_image)
    print(dcm_metadata_patient)
    print(dcm_metadata_series)
    print(dcm_metadata_study)
    payload = {
      'metadata_patient': dcm_metadata_patient,
      'metadata_study': dcm_metadata_study,
      'metadata_series': dcm_metadata_series,
      'metadata_image': dcm_metadata_image
    }
    headers = {
      'Content-Type': 'application/json'
    }
    url = os.environ.get('dicom-router-url')
    response = requests.post(url+'/dicom-upsert', json=payload, headers=headers)
    print(response)
    print(f"Successfully inserted {pathname}")
  except (InvalidDicomError, OperationFailure) as e:
    print(f"Error inserted {pathname}: {e}")

def dicom_deleted(pathname):
  # send delete request to dicom router api by patient id
  print("dicom_delete")
import os
import time
import threading
import requests
from ftplib import FTP
from pathlib import Path
import json
from datetime import datetime

class FTPProcessor:
  def __init__(self,
               ftp_host='ftp_server', 
               ftp_user='testuser', 
               ftp_pass='testpass', 
               ftp_dir='/home/testuser', 
               output_dir='ftp_data',
               webserver_url='http://localhost:8001/upload'):
      self.ftp_host = ftp_host
      self.ftp_user = ftp_user
      self.ftp_pass = ftp_pass
      self.ftp_dir = ftp_dir
      self.output_dir = Path(output_dir).resolve()
      self.output_dir.mkdir(parents=True, exist_ok=True)
      self.webserver_url = webserver_url

  def connect_ftp(self, retries=3, delay=5):
    # establish FTP connection with retries
    for attempt in range(retries):
      try:
        ftp = FTP(self.ftp_host)
        ftp.login(user=self.ftp_user, passwd=self.ftp_pass)
        ftp.cwd(self.ftp_dir)  # Ensure the FTP directory exists
        return ftp
      except Exception as e:
        print(f"Error connecting to FTP (attempt {attempt+1}): {e}")
        if attempt < retries - 1:
          time.sleep(delay)
        else:
          print("Max retries reached, could not connect to FTP.")
          return None

  def fetch_latest_file(self):
    # get the latest file from the FTP server
    try:
      ftp = self.connect_ftp()
      if not ftp:
        print("Could not connect to FTP server")
        return None

      try:
        print("Listing files:")
        files = ftp.nlst()
        print("Files found:", files)
        
        if not files:
          print("No files available on FTP server.")
          ftp.quit()
          return None

      except Exception as e:
        print(f"Error listing files: {e}")
        ftp.quit()
        return None

      # find most recent file
      # MDRM - command to preserve a file's date info after transfer
      latest_file = max(files, key=lambda f: ftp.sendcmd(f'MDTM {f}'))
      
      # download the file
      local_filepath = self.output_dir / latest_file
      with open(local_filepath, 'wb') as local_file:
        ftp.retrbinary(f'RETR {latest_file}', local_file.write)
      
      ftp.quit()
      print(f"Downloaded latest file: {latest_file}")
      return local_filepath
    
    except Exception as e:
      print(f"Error fetching FTP file: {e}")
      import traceback
      traceback.print_exc()
      return None
  
  def upload_file_to_ftp(self, local_file):
    try:
      ftp = self.connect_ftp()
      if ftp is None:
        print("Failed to establish FTP connection")
        return False
      
      print("Current FTP Working Directory:", ftp.pwd())
      try:
        print("Current Directory Contents:")
        print(ftp.nlst())
      except Exception as list_error:
        print(f"Could not list directory contents: {list_error}")
      
      filename = os.path.basename(local_file)
      
      with open(local_file, 'rb') as file:
        # STOR - command to upload
        ftp.storbinary(f'STOR {filename}', file)
      
      ftp.quit()
      print(f"Successfully uploaded file: {filename}")
      return True
    except Exception as e:
      print(f"Detailed error uploading file to FTP: {e}")
      import traceback
      traceback.print_exc()
      return False

  def send_file_to_webserver(self, filepath):
    # send file to webserver as multipart request
    try:
      with open(filepath, 'rb') as file:
        files = {'file': file}
        response = requests.post(self.webserver_url, files=files)
      if response.status_code == 200:
        print(f"Successfully sent file to webserver: {filepath}")
        return True
      else:
        print(f"Failed to send file. Status code: {response.status_code}")
        return False
    except Exception as e:
      print(f"Error sending file to webserver: {e}")
      return False

  def save_processed_data(self, data):
    try:
      filename = f"car_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
      filepath = self.output_dir / filename
      with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
      print(f"Saved processed data to: {filepath}")
      return filepath
    except Exception as e:
      print(f"Error saving processed data: {e}")
      return None

  def run_periodic_tasks(self, interval=30):
    while True:
      try:
        # get latest file and send to webserver
        latest_file = self.fetch_latest_file()
        if latest_file:
          if self.upload_file_to_ftp(latest_file):
            self.send_file_to_webserver(latest_file)
      except Exception as e:
        print(f"Error in periodic tasks: {e}")
      
      time.sleep(interval)

def start_ftp_processor(interval=30):
  # start the FTP file processor in a separate thread
  ftp_processor = FTPProcessor()
  thread = threading.Thread(
    target=ftp_processor.run_periodic_tasks, 
    kwargs={'interval': interval}, 
    daemon=True
  )
  thread.start()
  return thread
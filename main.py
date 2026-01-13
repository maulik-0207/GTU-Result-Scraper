"""
Author: @maulik-0207 (Github Username)
Date: 13/01/2026
Description: There is a bug in GTU result page, so here is a scraping tool to get whole class's result into excel sheet.
Demo: Watch YT video from readme.md file of the repo. 

Warning: This bug may be fixed in future and might not work.
"""
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Getting Driver Ready
options = ChromeOptions()
options.add_argument("--window-size=960,1080")
driver = webdriver.Chrome(options=options)
driver.get("https://www.gturesults.in/")

# Exam Selection
exam_selection = driver.find_element(By.ID, "ddlbatch")
dropdown = Select(exam_selection)
value = input("Enter Exam option's value: ")
dropdown.select_by_value(value)

# Enrollment number parts
fixed = input("Enter fixed part: ")
variable = input("Enter last number (099 or 221): ")

# Scraping Starts
for i in range(1, int(variable) + 1):
    
    # Building up enrollment number
    enroll_no = driver.find_element(By.ID, "txtenroll")
    enroll_no.clear()
    build_enroll = str(fixed) + str(i).zfill(len(str(variable))) 
    enroll_no.send_keys(str(build_enroll))
    
    # Giving password
    ps = driver.find_element(By.ID, "txtpassword")
    ps.clear()
    ps.send_keys("1234")    
    
    # Manual Captcha solving
    enter = input(f"Captcha for {build_enroll}: ")
    captcha = driver.find_element(By.ID, "CodeNumberTextBox")
    captcha.send_keys(enter)
    
    # Submitting the form
    btn = driver.find_element(By.ID, "btnSearch")
    btn.send_keys(Keys.ENTER)

    # Waiting for results
    try:
        wait = WebDriverWait(driver, 5)
        wait.until(
            EC.any_of(
                EC.presence_of_element_located((By.ID, "lblCGPA")),
                EC.presence_of_element_located((By.ID, "lblmsg"))
            )
        )
    except Exception:
        print(f"Error in {build_enroll}")
        continue
    
    if driver.find_elements(By.ID, "lblmsg") and \
        (
            driver.find_element(By.ID, "lblmsg").text.strip() == "Oppssss! Data not available." \
                or \
            driver.find_element(By.ID, "lblmsg").text.strip() == "ERROR: Incorrect captcha code, try again."
        ):
        print(f"No Data for {build_enroll}")
        continue
    
    # Scraping data
    name = driver.find_element(By.ID, "lblName").text.strip()
    enrollment_number = driver.find_element(By.ID, "lblExam").text.strip()
    current_sem_back = driver.find_element(By.ID, "lblCUPBack").text.strip()
    total_back = driver.find_element(By.ID, "lblTotalBack").text.strip()
    spi = driver.find_element(By.ID, "lblSPI").text.strip()
    cpi = driver.find_element(By.ID, "lblCPI").text.strip()
    cgpa = driver.find_element(By.ID, "lblCGPA").text.strip()
    
    # Storing Data
    file_path = "gtu_results.xlsx"
    if not os.path.exists(file_path):
        result_data = {
            'Name': [name],
            'Enrollment_No': [str(enrollment_number)],
            'Current_Sem_Back': [current_sem_back],
            'Total_Back': [total_back],
            'SPI': [spi],
            'CPI': [cpi],
            'CGPA': [cgpa]
        }
        data = pd.DataFrame(result_data)
    else:
        data = pd.read_excel(file_path)
        data["Enrollment_No"] = data["Enrollment_No"].astype(str)
        result_data = {
            'Name': name,
            'Enrollment_No': str(enrollment_number),
            'Current_Sem_Back': current_sem_back,
            'Total_Back': total_back,
            'SPI': spi,
            'CPI': cpi,
            'CGPA': cgpa
        }

        data.loc[len(data)] = result_data
    data.to_excel(file_path, index=False)
    print(f"Saved result for {enrollment_number}")

# Storing Summary to new sheet
file_path = "gtu_results.xlsx"
if os.path.exists(file_path):
    df  = pd.read_excel(file_path, dtype={"Enrollment_No": str})
    for col in ["SPI", "CPI", "CGPA", "Current_Sem_Back", "Total_Back"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    
    result_data_max = {
        'Name': "MAX",
        'Enrollment_No': " - ",
        'Current_Sem_Back': df["Current_Sem_Back"].max(),
        'Total_Back': df["Total_Back"].max(),
        'SPI':  df["SPI"].max(),
        'CPI': df["CPI"].max(),
        'CGPA': df["CGPA"].max()
    }
    result_data_min = {
        'Name': "MIN",
        'Enrollment_No': " - ",
        'Current_Sem_Back': df["Current_Sem_Back"].min(),
        'Total_Back': df["Total_Back"].min(),
        'SPI':  df["SPI"].min(),
        'CPI': df["CPI"].min(),
        'CGPA': df["CGPA"].min()
    }
    result_data_avg = {
        'Name': "AVG",
        'Enrollment_No': " - ",
        'Current_Sem_Back': round(df["Current_Sem_Back"].mean(), 2),
        'Total_Back': round(df["Total_Back"].mean(), 2),
        'SPI':  round(df["SPI"].mean(), 2),
        'CPI': round(df["CPI"].mean(), 2),
        'CGPA': round(df["CGPA"].mean(), 2)
    }
    result_data_fail = {
        'Name': "Total Failed Students",
        'Enrollment_No': " - ",
        'Current_Sem_Back': df[df["Current_Sem_Back"] > 0].shape[0],
        'Total_Back': 0,
        'SPI':  0,
        'CPI': 0,
        'CGPA': 0
    }
    df.loc[len(df)] = result_data_max
    df.loc[len(df)] = result_data_min
    df.loc[len(df)] = result_data_avg
    df.loc[len(df)] = result_data_fail
    
    df.to_excel(file_path, index=False)
    print("Summary sheet added successfully")

driver.close()
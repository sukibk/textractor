
# Textract for Waivers

## Short App Description:
The app is being created to solve the problem of manual waiver data entry from the website [FAA Waivers Issued](https://www.faa.gov/uas/commercial_operators/part_107_waivers/waivers_issued?page=0) into related Excel tables. Following a micro-service infrastructure, the overall goal of the app is to reduce the time and energy consumption of AUVSI research employees/interns. This will help the whole team have more resources for other projects and will build a good base for further automation work in other projects and areas.

The app will be hosted on the AWS platform and will utilize AWS services such as the powerful text analyzer Textract and S3 Storage (used for storing files needed for program execution and final results). The app will automate the whole process from scratch. The app can be executed on demand or set to be executed on an interval. Previously, interns and employees needed to go to the FAA website, check each PDF, and manually enter the data into corresponding fields in Excel tables. Now, the app does all this work automatically. It crawls the webpage and checks if there are any new waivers that need to be analyzed. If so, it downloads them to the cloud (so employees don’t have to dedicate any of their PC memory to this) and stores those files there. In the next phase, the app converts PDF viewers into computer-readable JSON objects which also get stored on AWS S3 service. Of course, the application checks if the objects already exist and if they do, it just skips them (this is one way the application was sped up since the initial version). At the end, the application pulls the JSON object from AWS S3 storage and converts them to a human-readable Excel file which also gets stored on S3 and it comes with versioning enabled (storing multiple versions of the same document in order not to lose any data while overriding).

## Done So Far:
1. Initial application which was doing all of the above locally:
    - Very slow
    - Required memory on the employee’s PC
2. Enabling cloud compatibility for the download part of the application:
    - Improved download speed
    - No memory requirements on the employee’s side for PDF files
    - Still slow overall
3. Demo for David K.
4. Enabling cloud compatibility for Textract action:
    - Largely improved execution time
    - No more space requirement on the employee’s PC (still a requirement for storing one final Excel file)
5. Demo for the whole team
6. Enabling cloud functionality for each phase of the application:
    - Execution time fixed by more than 90%
    - Everything is stored on the cloud (instead of the application itself for now)
7. Added check for the existing JSON and PDF files so now only the new waivers get pulled by the application and it doesn’t repeat the process for the existing files
8. Fixed bug where only the first line was stored for “Operations Authorized” and “List Of Waived Regulations by Section and Title”
9. Some minor bug fixes and code reformatting in preparation for stage 2 – Deployment

## To Do:
1. Figure out the best way to put the whole app on the cloud
2. Do further testing and app improvements until everybody can seamlessly and easily use the app
3. More code reformatting for faster execution time
4. Think about adding some simple frontend
5. Enable simple app configuration
6. Ensure app security
7. Push to deployment

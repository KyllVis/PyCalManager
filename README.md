# PyCalManager

PyCalManager is an automated appointment tool made in Python using Google Calendar and Google Gmail products/APIs.

This tool allows the user to be sent an email in a specific format, which then checks if that appointment time/date is available.
If it is available, then the appointment is created in Google Calendar and an email is sent back to that person confirming this.

If it is unavailable, then no appointment is created and an email is returned to the person informing them that it wasn't created.

The original email needs to be provided in the following format. Currently, the date is in Australian/EU format DD/MM/YYYY:
Name:
New Client:
Date of Appointment:
Time of Appointment:
Appointment Type:


# Requirements to run

GoogleAPI permissions for Gmail and Calendar. For support on enabling API's see "https://support.google.com/googleapi/answer/6158841?hl=en" or ask ChatGPT.

To run the packages outlined at the top of the .py script need to be installed.

At the beginning, certain details such as your appointments email address and time zones are required.

Once the script is run for the first time, it will ask you to log in to your Google account. This data is not sent anywhere and is just used to ensure you have Google API permissions.

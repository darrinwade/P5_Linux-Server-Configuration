# Wade's category results application


 version 1.0 09/07/2015

Installation (Zip file contents)
--------------------------------

The checked in Category.zip file contains the following files:

(01) application.py - Python file containing the bulk of the processing code for the category
             application project.  Basic "CRUD" database processing, functionality needed for
             routing to the various UI components, as well as that needed to authenticate
             a user is stored here.

(02) application_dbsetup.py - Python file containing the configuration and setup code needed to
             define and build out the category database.  Execution of this script results in
             the creation of three tables, (Owner, Category, and Item), defined in an sqlite
             database for this application.

(03) application_LoadAndSetupCode.py - Python file used in the mid to late stateges of the
             category application's development to ensure the correct setup of the database
             tables, for the insertion/removal of data for the appropriate level of testing,
             and other misc uses.  Depending on the final state of testing, the contents of
             the script may or may not have "relevent" value.

(04) category.db - SQLite database created as the result of the successful execution of the
             application_dbsetup.py Python script.  It is the database for the application.
             If it does not exist, it can/should be created as the first step via execution
             of the application_dbsetup.py script.

(05) client_secrets.json - Credentials file downloaded from Google's developer sight used in
             the authentication and authorization portion of the application.

(06) static\main.css - Cascading style sheet for the application.

(07) templates\categoriesAll.html - UI component used for displaying the category list information.
             It is the "home page" of the application, handles the primary routing for adding,
             changing, and deleting categories, shows both individual and "group" JSON category
             information, and handles the routing for category's items.

(08) templates\categoryCreate.html - UI component used in the creation of a category element

(09) templates\categoryDelete.html - UI component used in the deletion of a category element

(10) templates\categoryEdit.html - UI component used in the editing of a category element

(11) templates\categoryItemAll.html - UI component used for the display of all item entries for a
             given category element.  It also handles the primary routing for adding, changing,
             and deleting category items in addition to showing both individual and "group"
             JSON category item information.

(12) templates\categoryItemAllLastCreated.html - UI component used for the display the last 
             20 catogory items regardles of the individual category it belongs to.

(13) templates\categoryItemCreate.html - UI component used in the creation of a category item element

(14) templates\categoryItemDelete.html - UI component used in the deletion of a category item element

(15) templates\categoryItemEdit.html - UI component used in the editing of a category item element

(16) templates\categoryItemView.html - UI component used in the viewing of a category item element

(17) templates\categoryView.html - UI component used in the viewing of a category element

(18) templates\login.html - UI component used for processing user logins

_____________________________________________________________________________________________


In order test/run the category application, perform the following steps:

(01) Unzip the contents of the tournanment.zip into the vagrant subdirectory (It's a folder)
(02) Start the GIT Bash application
(03) CD to the fullstack/vagrant directory structure
(04) Type vagrant up <enter> at the command line
(05) Type vagrant ssh <enter> at the command line
(06) CD to the /vagrant/category virtural directory 
(07  If there isn't already a category.db database, type "python application_dbsetup.py" to create one.
(07) At the vagrant command line, type "python application.py"
(08) Using a standard browser, you should be able to access the application "home page"
     by typing http://localhost:8080/CatalogApp, http://localhost:8080/Catalog, or
     http://localhost:8080/ <Enter> on the URL.
     
 From there you can begin viewing any existing category and associated item entries or you can
 look to add your own category entries once you've logged into the application.  Authourization
 is granted through Google so a valid Google account id is required.



Copyright 2015 Wade Corporation.  All rights reserved.
Wade's Tournament Results Application and its use are subject to a license agreement and are
also subject to copyright, trademark, patent and/or other laws.
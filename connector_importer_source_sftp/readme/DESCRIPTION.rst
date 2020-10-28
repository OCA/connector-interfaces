Add import source capable of loading files from SFTP.

Source type provided at the moment: CSV.

Special feature: move files to another path when the import is finished.

You can configure input, error, success path.

Files are searched into input folder and if the flag `move_file_after_import`
is enabled, the file will be moved to error or success path
depending on the result of the import process.

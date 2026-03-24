from IPython.display import display
import ipywidgets as widgets

def select_file(title="Select a file", file_types=["*"]):
    """
    Opens a file selection dialog and returns the selected file path.
    
    Parameters:
    - title: The title of the file selection dialog.
    - file_types: A list of allowed file types (e.g., ["*.txt", "*.csv"]).
    
    Returns:
    - The path of the selected file, or None if no file was selected.
    """
    # Create a FileUpload widget
    uploader = widgets.FileUpload(accept=",".join(file_types), multiple=False)
    
    # Display the widget
    display(widgets.HTML(f"<h3>{title}</h3>"), uploader)
    
    # Wait for the user to upload a file
    while not uploader.value:
        pass  # Wait until a file is uploaded
    
    # Get the uploaded file's name and content
    uploaded_file = next(iter(uploader.value.values()))
    file_name = uploaded_file['metadata']['name']
    
    return file_name
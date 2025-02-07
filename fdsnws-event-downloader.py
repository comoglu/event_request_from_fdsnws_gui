import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QComboBox, QPushButton, QLabel, QTableWidget,
                           QTableWidgetItem, QDateTimeEdit, QFormLayout,
                           QMessageBox, QFileDialog, QHBoxLayout, QMenuBar, 
                           QMenu, QAction, QDialog, QTextBrowser, QVBoxLayout,
                           QStatusBar)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QDateTime

import obspy
from obspy.clients.fdsn import Client
from obspy.core import UTCDateTime
import pandas as pd

class EventWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Event List")
        self.setGeometry(300, 300, 1000, 600)
        
        # Set a modern font
        font = QFont()
        font.setFamily('Arial')
        self.setFont(font)
        
        layout = QVBoxLayout()
        
        # Create table for events with improved styling
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Time", "Magnitude", "Latitude", "Longitude", "Depth (km)", "Description"
        ])
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        
        # Create save section
        save_layout = QHBoxLayout()
        
        # Input format selection
        self.input_format_label = QLabel("Input Format:")
        self.input_format_combo = QComboBox()
        self.input_format_combo.addItems([
            "QUAKEML", "SC3ML", "NORDIC", "CMTSOLUTION", 
            "PICKEL", "JSON", "CSV", "ZMAP"
        ])
        self.input_format_combo.setToolTip("Select the input format of the events")
        
        # Output format selection
        self.output_format_label = QLabel("Output Format:")
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems([
            "QUAKEML", "SC3ML", "NORDIC", "CMTSOLUTION", 
            "PICKEL", "JSON", "CSV", "ZMAP"
        ])
        self.output_format_combo.setToolTip("Select the output format to save events")
        
        # Save button
        self.save_button = QPushButton("Save Selected Events")
        self.save_button.clicked.connect(self.save_events)
        self.save_button.setToolTip("Save the selected events in the chosen format")
        
        # Add widgets to save layout
        save_layout.addWidget(self.input_format_label)
        save_layout.addWidget(self.input_format_combo)
        save_layout.addWidget(self.output_format_label)
        save_layout.addWidget(self.output_format_combo)
        save_layout.addWidget(self.save_button)
        
        layout.addWidget(self.table)
        layout.addLayout(save_layout)
        self.setLayout(layout)
        
        self.catalog = None

    def display_events(self, catalog):
        self.catalog = catalog
        self.table.setRowCount(len(catalog))
        
        for i, event in enumerate(catalog):
            origin = event.origins[0] if event.origins else None
            magnitude = event.magnitudes[0] if event.magnitudes else None
            
            # Safety checks to prevent errors
            time_str = origin.time.strftime("%Y-%m-%d %H:%M:%S") if origin and origin.time else "N/A"
            mag_str = f"{magnitude.mag:.1f}" if magnitude and magnitude.mag is not None else "N/A"
            lat_str = f"{origin.latitude:.3f}" if origin and origin.latitude is not None else "N/A"
            lon_str = f"{origin.longitude:.3f}" if origin and origin.longitude is not None else "N/A"
            depth_str = f"{origin.depth/1000:.1f}" if origin and origin.depth is not None else "N/A"
            desc_str = event.event_descriptions[0].text if event.event_descriptions else ""
            
            # Create table items
            time_item = QTableWidgetItem(time_str)
            mag_item = QTableWidgetItem(mag_str)
            lat_item = QTableWidgetItem(lat_str)
            lon_item = QTableWidgetItem(lon_str)
            depth_item = QTableWidgetItem(depth_str)
            desc_item = QTableWidgetItem(desc_str)
            
            # Set items to the table
            self.table.setItem(i, 0, time_item)
            self.table.setItem(i, 1, mag_item)
            self.table.setItem(i, 2, lat_item)
            self.table.setItem(i, 3, lon_item)
            self.table.setItem(i, 4, depth_item)
            self.table.setItem(i, 5, desc_item)
            
        self.table.resizeColumnsToContents()

    def save_events(self):
        if not self.catalog:
            QMessageBox.warning(self, "Warning", "No events to save")
            return
            
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select events to save")
            return
    
        # Prepare selected events
        selected_events = obspy.Catalog()
        for row in selected_rows:
            selected_events.append(self.catalog[row])
    
        # Get input and output formats
        input_format = self.input_format_combo.currentText().upper()
        output_format = self.output_format_combo.currentText().upper()
    
        # Determine file extension based on output format
        format_extensions = {
            "QUAKEML": ".xml",
            "SC3ML": ".sc3ml",
            "NORDIC": ".out",
            "CMTSOLUTION": ".txt",
            "PICKEL": ".pkl",
            "JSON": ".json",
            "CSV": ".csv",
            "ZMAP": ".zmap"
        }
    
        # File save dialog
        output_file, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Events", 
            "", 
            f"{output_format} Files (*{format_extensions[output_format]})"
        )
    
        if not output_file:
            return
    
        try:
            # Check if the output format is supported
            supported_formats = [
                "QUAKEML", "SC3ML", "NORDIC", "CMTSOLUTION", 
                "PICKEL", "JSON", "CSV", "ZMAP"
            ]
        
            if output_format not in supported_formats:
                QMessageBox.warning(self, "Unsupported Format", 
                                    f"Format {output_format} is not supported. Skipping conversion.")
                return
        
            # Special handling for CSV output
            if output_format == "CSV":
                data = []
                for event in selected_events:
                    origin = event.origins[0] if event.origins else None
                    magnitude = event.magnitudes[0] if event.magnitudes else None
                    event_dict = {
                        'event_id': str(event.resource_id),
                        'time': str(origin.time) if origin and origin.time else None,
                        'latitude': origin.latitude if origin else None,
                        'longitude': origin.longitude if origin else None,
                        'depth_km': origin.depth/1000 if origin and origin.depth else None,
                        'magnitude': magnitude.mag if magnitude else None,
                        'magnitude_type': magnitude.magnitude_type if magnitude else None,
                        'description': event.event_descriptions[0].text 
                        if event.event_descriptions else None
                    }
                    data.append(event_dict)
                pd.DataFrame(data).to_csv(output_file, index=False)
            elif output_format == "ZMAP":
                # Custom ZMAP format writing
                with open(output_file, 'w') as f:
                    for event in selected_events:
                        origin = event.origins[0] if event.origins else None
                        magnitude = event.magnitudes[0] if event.magnitudes else None
                        if origin and magnitude:
                            f.write(f"{origin.time.year} {origin.time.month} {origin.time.day} "
                                   f"{origin.time.hour} {origin.time.minute} {origin.time.second} "
                                   f"{origin.latitude:.3f} {origin.longitude:.3f} "
                                   f"{origin.depth/1000:.1f} {magnitude.mag}\n")
            else:
                # Use ObsPy's write method for other formats
                try:
                    selected_events.write(output_file, format=output_format)
                except Exception as convert_error:
                    QMessageBox.warning(self, "Conversion Error", 
                                        f"Could not convert to {output_format}: {str(convert_error)}")
                    return
        
            QMessageBox.information(self, "Success", 
                f"Events saved to {output_file} in {output_format} format")
    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save events: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FDSN Event Fetcher")
        self.setGeometry(100, 100, 500, 350)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QFormLayout()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create status bar
        self.statusBar().showMessage('Ready')
        
        # FDSN datacenter dropdown
        self.datacenter_combo = QComboBox()
        self.datacenter_combo.addItems([
            "IRIS", "USGS", "EMSC", "GFZ","NOA","INGV", "NCEDC", "SCEDC",
            "GEOFON", "ISC", "ETHZ", "GEONET", "ICGC", "IESDMC", "KNMI",
            "LMU", "NERIES", "ODC", "ORFEUS", "RESIF", "SCEDC", "USP"
        ])
        self.datacenter_combo.setToolTip("Select the FDSN data center")
        
        # Date/time selection
        self.start_time = QDateTimeEdit()
        self.start_time.setDateTime(QDateTime.currentDateTime().addDays(-7))
        self.start_time.setCalendarPopup(True)
        self.start_time.setToolTip("Select the start time for event search")
        
        self.end_time = QDateTimeEdit()
        self.end_time.setDateTime(QDateTime.currentDateTime())
        self.end_time.setCalendarPopup(True)
        self.end_time.setToolTip("Select the end time for event search")
        
        # Magnitude range
        self.min_magnitude = QComboBox()
        self.min_magnitude.addItems([str(i/10) for i in range(0, 91, 5)])
        self.min_magnitude.setCurrentText("5.0")
        self.min_magnitude.setToolTip("Select the minimum magnitude for events")
        
        # Fetch button
        self.fetch_button = QPushButton("Fetch Events")
        self.fetch_button.clicked.connect(self.fetch_events)
        self.fetch_button.setToolTip("Retrieve events based on selected criteria")
        
        # Add widgets to layout
        layout.addRow("FDSN Datacenter:", self.datacenter_combo)
        layout.addRow("Start Time:", self.start_time)
        layout.addRow("End Time:", self.end_time)
        layout.addRow("Minimum Magnitude:", self.min_magnitude)
        layout.addRow(self.fetch_button)
        
        central_widget.setLayout(layout)
        
        # Create event window
        self.event_window = EventWindow()

    def create_menu_bar(self):
        # Create menu bar
        menubar = self.menuBar()
        
        # Create Help menu
        help_menu = menubar.addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def show_about_dialog(self):
        # Create About dialog
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About FDSN Event Fetcher")
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create text browser for about information
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        
        # Set HTML formatted about text
        about_text = """
        <h2>FDSN Event Fetcher</h2>
        <p><strong>Version:</strong> 0.1</p>
        <p><strong>Author:</strong> Mustafa Comoglu</p>
        <p><strong>GitHub Repository:</strong> 
        <a href='https://github.com/comoglu/event_request_from_fdsnws_gui'>
        comoglu/event_request_from_fdsnws_gui</a></p>
        <p>A GUI tool for fetching and saving seismic events from FDSN Web Services.</p>
        <p>Built using Python, PyQt5, and ObsPy.</p>
        <p><em>Developed to simplify seismic event data retrieval and management.</em></p>
        """
        
        text_browser.setHtml(about_text)
        
        # Add text browser to layout
        layout.addWidget(text_browser)
        
        # OK button
        close_button = QPushButton("Close")
        close_button.clicked.connect(about_dialog.close)
        layout.addWidget(close_button)
        
        # Set layout
        about_dialog.setLayout(layout)
        
        # Resize and show dialog
        about_dialog.resize(400, 300)
        about_dialog.exec_()

    def fetch_events(self):
        try:
            # Update status bar
            self.statusBar().showMessage('Fetching events...')
            
            client = Client(self.datacenter_combo.currentText())
            
            starttime = UTCDateTime(self.start_time.dateTime().toPyDateTime())
            endtime = UTCDateTime(self.end_time.dateTime().toPyDateTime())
            minmagnitude = float(self.min_magnitude.currentText())
            
            # Comprehensive set of parameters to try
            optional_params = [
                {'includeallorigins': True},
                {'includeallmagnitudes': True},
                {'includearrivals': True},
                {'includeamplitudes': True}
            ]
            
            # Base parameters
            params = {
                'starttime': starttime,
                'endtime': endtime,
                'minmagnitude': minmagnitude
            }
            
            # Try adding optional parameters
            for optional_param in optional_params:
                try:
                    # Create a copy of base parameters and update with optional parameter
                    current_params = params.copy()
                    current_params.update(optional_param)
                    
                    # Try to fetch events with current parameters
                    catalog = client.get_events(**current_params)
                    
                    # If successful, break the loop
                    break
                except Exception as param_error:
                    # Log the parameter that wasn't supported
                    print(f"Parameter {list(optional_param.keys())[0]} not supported: {param_error}")
                    continue
            else:
                # If no optional parameters work, fetch with base parameters
                catalog = client.get_events(**params)
            
            # Update status bar
            self.statusBar().showMessage(f'Fetched {len(catalog)} events')
            
            # Count additional metadata
            total_origins = sum(len(event.origins) for event in catalog)
            total_magnitudes = sum(len(event.magnitudes) for event in catalog)
            total_picks = sum(len(event.picks) for event in catalog)
            total_amplitudes = sum(len(event.amplitudes) for event in catalog)
            
            # Provide detailed information in a message box
            info_text = (f"Fetched {len(catalog)} events\n"
                        f"Total Origins: {total_origins}\n"
                        f"Total Magnitudes: {total_magnitudes}\n"
                        f"Total Picks: {total_picks}\n"
                        f"Total Amplitudes: {total_amplitudes}")
            QMessageBox.information(self, "Fetch Details", info_text)
            
            # Display events in the event window
            self.event_window.display_events(catalog)
            self.event_window.show()
        
        except Exception as e:
            # Catch any unexpected errors
            self.statusBar().showMessage('Error occurred')
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

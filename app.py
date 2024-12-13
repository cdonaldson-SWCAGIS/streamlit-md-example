import logging
import requests
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Optional: Configure logging (remove if not needed)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_URL = "https://www.ag-grid.com/example-assets/master-detail-data.json"

@st.cache_data
def load_data(url: str):
    """Load JSON data from the given URL and return a DataFrame and raw JSON."""
    response = requests.get(url)
    data = response.json()
    df = pd.read_json(url)
    # Normalize the callRecords column
    df["callRecords"] = df["callRecords"].apply(lambda x: pd.json_normalize(x))
    
    # Insert orphaned records
    orphaned_records = {
        "name": ["Orphaned Record"],
        "account": ["N/A"],
        "calls": [0],
        "minutes": [0],
        "callRecords": [pd.DataFrame([
            {"callId": "orphan1", "direction": "outbound", "number": "1234567890", "duration": 0, "switchCode": "N/A"},
            {"callId": "orphan2", "direction": "inbound", "number": "0987654321", "duration": 0, "switchCode": "N/A"}
        ])]
    }
    df = pd.concat([df, pd.DataFrame(orphaned_records)], ignore_index=True)
    
    return df, data

def build_grid_options(data_json):
    """
    Build and return the gridOptions dictionary for the AgGrid.
    
    This configuration sets up a master-detail grid:
    - The main grid shows master rows.
    - Expanding a row shows the detail grid of `callRecords`.
    """
    # JavaScript code for getDetailRowData callback
    get_detail_js = JsCode(
        """function (params) {
            params.successCallback(params.data.callRecords);
        }"""
    )
    
    gridOptions = {
        # Enable Master/Detail view
        "masterDetail": True,
        "rowSelection": "single",
        # Main grid columns
        "columnDefs": [
            {
                "field": "name",
                "cellRenderer": "agGroupCellRenderer",
                "checkboxSelection": True,
            },
            {"field": "account"},
            {"field": "calls"},
            {"field": "minutes", "valueFormatter": "x.toLocaleString() + 'm'"},
        ],
        "defaultColDef": {
            "flex": 1,
        },
        # Detail Cell Renderer Parameters
        "detailCellRendererParams": {
            "detailGridOptions": {
                "rowSelection": "multiple",
                "suppressRowClickSelection": True,
                "enableRangeSelection": True,
                "pagination": True,
                "paginationAutoPageSize": True,
                "columnDefs": [
                    {"field": "callId", "checkboxSelection": True},
                    {"field": "direction"},
                    {"field": "number", "minWidth": 150},
                    {"field": "duration", "valueFormatter": "x.toLocaleString() + 's'"},
                    {"field": "switchCode", "minWidth": 150},
                ],
                "defaultColDef": {
                    "sortable": True,
                    "flex": 1,
                },
            },
            "getDetailRowData": get_detail_js,
        },
        # Row Data for the master grid
        "rowData": data_json + [{
            "name": "Orphans", 
            "account": 0, 
            "calls": 0, 
            "minutes": 0, 
            "callRecords": [
                {"callId": "orphan1", "direction": "outbound", "number": "1234567890", "duration": 0, "switchCode": "N/A"},
                {"callId": "orphan2", "direction": "inbound", "number": "0987654321", "duration": 0, "switchCode": "N/A"}
            ]
        }]
    }
    return gridOptions

def main():
    st.title("Master-Detail Grid Example")

    # Load data
    logger.info("Loading data...")
    df, data_json = load_data(DATA_URL)
    logger.info("Data loaded successfully.")

    # Build grid options for the master-detail grid
    logger.info("Building grid options...")
    gridOptions = build_grid_options(data_json)
    logger.info("Grid options built.")

    # Create tabs for different views
    tabs = st.tabs(["Grid", "Underlying Data", "Grid Options", "Grid Return"])

    with tabs[0]:
        # Render the AgGrid with given gridOptions
        response = AgGrid(
            None,  # No dataframe, using rowData in gridOptions directly
            gridOptions=gridOptions,
            allow_unsafe_jscode=True,
            enable_enterprise_modules=True,
            key="an_unique_key",
        )

    with tabs[1]:
        # Show the underlying JSON data
        st.write(data_json)

    with tabs[2]:
        # Show the gridOptions configuration
        st.write(gridOptions)

    # Show selected rows ID (if any)
    st.write("Selected Rows ID:", response.selected_rows_id)

if __name__ == "__main__":
    main()

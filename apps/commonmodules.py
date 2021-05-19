# Usual Dash dependencies
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import dash
from dash.exceptions import PreventUpdate
import pandas as pd

# Let us import the app object in case we need to define
# callbacks here
from app import app

# CSS Styling for the NavLink components
navlink_style = {
    'color': '#fff'
}

navbar = dbc.Navbar(
    [
        html.A(
            # Use row and col to control vertical alignment of logo / brand
            dbc.Row(
                [
                    dbc.Col(dbc.NavbarBrand("IE 156 Case App", className="ml-2")),
                ],
                align="center",
                no_gutters=True,
            ),
            href="/home",
        ),
        dbc.NavLink("Home", href="/home", style=navlink_style),
        dbc.NavLink("Movies", href="/movies/movies_home", style=navlink_style),
        dbc.NavLink("Genres", href="/genres", style=navlink_style),
    ],
    dark=True,
    color='dark'
)
# Usual Dash dependencies
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd

# Let us import the app object in case we need to define
# callbacks here
from app import app
#for DB needs
from apps import dbconnect as db


# store the layout objects into a variable named layout
layout = html.Div(
    [
        html.H2('Movies'), # Page Header
        html.Hr(),
        dbc.Card( # Card Container
            [
                dbc.CardHeader( # Define Card Header
                    [
                        html.H3('Manage Records')
                    ]
                ),
                dbc.CardBody( # Define Card Contents
                    [
                        html.Div( # Add Movie Btn
                            [
                                # Add movie button will work like a 
                                # hyperlink that leads to another page
                                dbc.Button(
                                    "Add Movie",
                                    href='/movies/movies_profile?mode=add'
                                )
                            ]
                        ),
                        html.Hr(),
                        html.Div( # Create section to show list of movies
                            [
                                html.H4('Find Movies'),
                                html.Div(
                                    dbc.Form(
                                        dbc.FormGroup(
                                            [
                                                dbc.Label("Search Title", width=1),
                                                dbc.Col(
                                                    dbc.Input(
                                                        type='text',
                                                        id='moviehome_titlefilter',
                                                        placeholder='Movie Title'
                                                    ),
                                                    width=5
                                                )
                                            ],
                                            row=True
                                        )
                                    )
                                ),
                                html.Div(
                                    "Table with movies will go here.",
                                    id='moviehome_movielist'
                                )
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)

@app.callback(
    [
        Output('moviehome_movielist', 'children')
    ],
    [
        Input('url', 'pathname'),
        Input('moviehome_titlefilter', 'value') # add this
    ]
)
def moviehome_loadmovielist(pathname, filter_title): # add the corresponding variable too
    if pathname == '/movies/movies_home':
        # 1. SQL Query to get the records

        # added the movie_id for the query since we need it
        # to generate the hyperlinks
        sql = """ SELECT movie_id, movie_name, genre_name
            FROM movies m
                INNER JOIN genres g ON m.genre_id = g.genre_id
            WHERE movie_delete_ind = false
        """
        values = [] # blank since I do not have placeholders in my SQL
        
        # Effectively, we add another condition to the SQL query
        # if the variable filter_title is not empty
        if filter_title:

            # We use the ILIKE operator to perform pattern-matching on text
            sql += " AND movie_name ILIKE %s"

            # The we add % at the beginning and end of the filter
            # string to denote that there can be text before or 
            # after the filter string
            values += [f"%{filter_title}%"]


        cols = ['ID', 'Movie Title', 'Genre']

        df = db.querydatafromdatabase(sql, values, cols)

        
        if df.shape[0]: # if (rows in dataframe) > 0

            # Create the hyperlinks
            linkcolumn = {}
            for index, row in df.iterrows():
                linkcolumn[index] = dcc.Link(
                    'Edit', 
                    href='/movies/movies_profile?mode=edit&movieid='+str(row["ID"])
                )

            # Name the column of hyperlinks -- Action
            dictionarydata = {'Action': linkcolumn}

            # Add the column to the existing dataframe
            data_dict = df.to_dict()
            data_dict.update(dictionarydata)
            df = pd.DataFrame.from_dict(data_dict)

            # Filter and organize the columns to display
            # We do not need to display the movie_id column
            df = df[['Movie Title', 'Genre', 'Action']]
        
        # 2. Create the html element to return to the Div

        table = dbc.Table.from_dataframe(df, striped=True, bordered=True,
                hover=True, size='sm')
        
        if df.shape[0]:
            return [table]
        else:
            return ['No records to display']

    else:
        raise PreventUpdate
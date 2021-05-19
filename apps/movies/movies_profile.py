# Usual Dash dependencies
from re import M
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table
import dash
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
from urllib.parse import urlparse, parse_qs

# Let us import the app object in case we need to define
# callbacks here
from app import app
#for DB needs
from apps import dbconnect as db


# store the layout objects into a variable named layout
layout = html.Div(
    [
        html.Div( # This div shall contain all dcc.Store objects
            [
                dcc.Store(id='movieprofile_toload', storage_type='memory', data=0),
            ]
        ),
        html.H2('Movie Details'), # Page Header
        html.Hr(),
        dbc.Alert(id='movieprofile_alert', is_open=False), # For feedback purposes
        dbc.Form(
            [
                dbc.FormGroup(
                    [
                        dbc.Label("Title", width=1),
                        dbc.Col(
                            dbc.Input(
                                type='text', 
                                id='movieprofile_title',
                                placeholder="Title"
                            ),
                            width=5
                        )
                    ],
                    row=True # Makes sure the label and the field are in a row
                ),
                dbc.FormGroup(
                    [
                        dbc.Label("Genre", width=1),
                        dbc.Col(
                            dcc.Dropdown(
                                id='movieprofile_genre',
                                placeholder='Genre'
                            ),
                            width=5
                        )
                    ],
                    row=True
                ),
                dbc.FormGroup(
                    [
                        dbc.Label("Release Date", width=1),
                        dbc.Col(
                            dcc.DatePickerSingle(
                                id='movieprofile_releasedate',
                                placeholder='Release Date',
                                month_format='MMM Do, YY',
                            ),
                            width=5
                        )
                    ],
                    row=True 
                ),
            ]
        ),
        html.Div(
            [
                dbc.Form(
                    dbc.FormGroup(
                        [
                            dbc.Checklist(
                                id='movieprofile_removerecord',
                                options=[
                                    {
                                        'label': "Mark for Deletion",
                                        'value': 1
                                    }
                                ],
                                # I want the label to be bold
                                style={'fontWeight':'bold'}, 
                            )
                        ]
                    )
                )
            ],
            id='movieprofile_remove_div',
            # Let's hide this initially
            # Only show contents of this div if mode=edit
            style={'display':'none'}
        ),
        dbc.Button(
            'Submit',
            id='movieprofile_submit',
            n_clicks=0 # Initialize number of clicks
        ),
        dbc.Modal( # Modal = dialog box; feedback for successful saving.
            [
                dbc.ModalHeader(
                    html.H4('Save Success')
                ),
                dbc.ModalBody(
                    'Message here! Edit me please!'
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Proceed",
                        href='/movies/movies_home' # Clicking this would lead to a change of pages
                    )
                )
            ],
            centered=True,
            id='movieprofile_successmodal',
            backdrop='static' # Dialog box does not go away if you click at the background
        )
    ]
)

@app.callback(
    [
        Output('movieprofile_genre', 'options'),
        Output('movieprofile_toload', 'data'),
        # Based on the create_mode in the URL, we would
        # like to set the style for the div that contains the
        # removal checkbox
        Output('movieprofile_remove_div', 'style')
    ],
    [
        Input('url', 'pathname')
    ],
    [
        State('url', 'search')
    ]
)
def movieprofile_populategenres(pathname, search):
    # No need for CTX for pathname triggers
    if pathname == '/movies/movies_profile':
        sql = """
        SELECT genre_name as label, genre_id as value
        FROM genres 
        WHERE genre_delete_ind = False
        """
        values = []
        cols = ['label', 'value']

        df = db.querydatafromdatabase(sql, values, cols)

        genre_options = df.to_dict('records')

        # Are we on add or edit mode?
        parsed = urlparse(search)
        create_mode = parse_qs(parsed.query)['mode'][0]
        to_load = 1 if create_mode == 'edit' else 0


        # If create_mode is edit, then we have to show the remove_div
        if create_mode == 'edit':
            remove_div_style = {'display': 'unset'}
        else:
            remove_div_style = {'display': 'none'}

        return [genre_options, to_load, remove_div_style]

    else:
        # If the pathname is not the desired,
        # this callback does not execute
        raise PreventUpdate


@app.callback(
    [
        Output('movieprofile_title', 'value'),
        Output('movieprofile_genre', 'value'),
        Output('movieprofile_releasedate', 'date'),
    ],
    [
        Input('movieprofile_toload', 'modified_timestamp')
    ],
    [
        State('movieprofile_toload', 'data'),
        State('url', 'search'),
    ]
)
def movieprofile_loadprofile(timestamp, toload, search):
    if toload: # check if toload = 1
        
        # Get movieid value
        parsed = urlparse(search)
        movieid = parse_qs(parsed.query)['movieid'][0]

        # Query from db
        sql = """
            SELECT movie_name, genre_id, movie_release_date
            FROM movies
            WHERE movie_id = %s
        """
        values = [movieid]
        col = ['moviename', 'genreid', 'releasedate']

        df = db.querydatafromdatabase(sql, values, col)

        moviename = df['moviename'][0]
        # Our dropdown list has the genreids as values then it will 
        # display the correspoinding labels
        genreid = int(df['genreid'][0])
        releasedate = df['releasedate'][0]

        return [moviename, genreid, releasedate]

    else:
        raise PreventUpdate


@app.callback(
    [
        Output('movieprofile_alert', 'color'),
        Output('movieprofile_alert', 'children'),
        Output('movieprofile_alert', 'is_open'),
        Output('movieprofile_successmodal', 'is_open')
    ],
    [
        Input('movieprofile_submit', 'n_clicks')
    ],
    [
        State('movieprofile_title', 'value'),
        State('movieprofile_genre', 'value'),
        State('movieprofile_releasedate', 'date'),
        State('url', 'search'),
        # Add the value of the dbc.Checklist object as a state
        State('movieprofile_removerecord', 'value')
    ]
)
def movieprofile_saveprofile(submitbtn, title, genre, releasedate,
                             search, remove_checked):
    ctx = dash.callback_context
    # The ctx filter -- ensures that only a change in url will activate this callback
    if ctx.triggered:
        eventid = ctx.triggered[0]['prop_id'].split('.')[0]
        if eventid == 'movieprofile_submit' and submitbtn:
            # the submitbtn condition checks if the callback was indeed activated by a click
            # and not by having the submit button appear in the layout

            # Set default outputs
            alert_open = False
            modal_open = False
            alert_color = ''
            alert_text = ''

            # We need to check inputs
            if not title: # If title is blank, not title = True
                alert_open = True
                alert_color = 'danger'
                alert_text = 'Check your inputs. Please supply the movie title.'
            elif not genre:
                alert_open = True
                alert_color = 'danger'
                alert_text = 'Check your inputs. Please supply the movie genre.'
            elif not releasedate:
                alert_open = True
                alert_color = 'danger'
                alert_text = 'Check your inputs. Please supply the movie release date.'
            else: # all inputs are valid
                
                # This is to extract the value corresponding 'mode'
                # from the URL
                parsed = urlparse(search)
                create_mode = parse_qs(parsed.query)['mode'][0]

                if create_mode == 'add': # INSERT in add mode

                    # Add the data into the db

                    sql = '''
                        INSERT INTO movies (movie_name, genre_id,
                            movie_release_date, movie_delete_ind)
                        VALUES (%s, %s, %s, %s)
                    '''
                    values = [title, genre, releasedate, False]

                    db.modifydatabase(sql, values)

                elif create_mode == 'edit': # UPDATE in edit mode
                    
                    # Get movieid to edit
                    # parsed = urlparse(search) -- > no need, already defined this above
                    movieid = int(parse_qs(parsed.query)['movieid'][0])

                    # Create SQL scripts

                    # Modify the script to update the 
                    # movie_delete_ind attribute
                    sql = '''
                        UPDATE movies 
                        SET
                            movie_name = %s, 
                            genre_id = %s,
                            movie_release_date = %s,
                            movie_delete_ind = %s
                        WHERE
                            movie_id = %s
                    '''

                    # The variable 'remove_checked' contains the 
                    # value of the dbc.Checklist field

                    # For a dbc.Checklist object, the 'value' is 
                    # a LIST of items which were checked by users

                    # For our case, if we do not mark as delete, remove_checked = []
                    # If we mark as delete, remove_checked = [1]
                    # This is because we defined the value of the option as 1

                    # The movie_delete_ind is a boolean attribute
                    # We need to convert remove_checked to a boolean data type

                    delete_ind = bool(remove_checked)
                    # If remove_checked = [], bool(remove_checked) = False
                    # If remove_checked has any content, bool(remove_checked) = True

                    # Put the value for the delete_ind into the values
                    values = [title, genre, releasedate, delete_ind, movieid]

                    db.modifydatabase(sql, values)
                    

                else: # none of the above
                    raise PreventUpdate
                    # or other responses to wrong URLs
                    

                # If this is successful, we want the successmodal to show
                modal_open = True

            return [alert_color, alert_text, alert_open, modal_open]

        else: # Callback was not triggered by desired triggers
            raise PreventUpdate

    else:
        raise PreventUpdate
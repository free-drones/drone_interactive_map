/**
 * Application file. Loads and directs the entire React application
 */
import React from "react";
import {
    BrowserRouter as Router,
    Switch,
    Route,
    Redirect
  } from "react-router-dom";
import Main from './Main/Main.js';
import StartUp from './Startup/StartUp.js';
import { createMuiTheme, ThemeProvider } from '@material-ui/core/styles';

import ServerConnection from './Connection/ServerConnection.js';
import MockupConstants from './Connection/MockupConstants.js';

import Storage from './Storage.js';

/**
 * Theme for components. To use, wrap component in a <ThemeProvider theme={theme}>.
 */
const theme = createMuiTheme({
    palette: {
        primary: {
            main: '#303f9f' // Indigo
        },
        secondary: {
            main: '#1976d2' // Blue
        },


        success: {
            main: '#4caf50' // MUI default green
        },
        info: {
            main: '#2196f3' // MUI default blue
        },
        warning: {
            main: '#ff9800' // MUI default yellow
        },
        error: {
            main: '#f44336' // MUI default red
        },


        accept: {
            main: '#4caf50' // MUI default green
        },
        decline: {
            main: '#f44336' // MUI default red
        },
    }
});

/**
 * Testing flag, set to true if using mockup server.
 */
const TESTING = true;

if (TESTING) {
    ServerConnection.initialize(MockupConstants.LOCAL_HOST, MockupConstants.PORT, MockupConstants.NAMESPACE);
}
else {
    window.onerror = function (message, file, line, col, error) {
        // Remove the beginning 'http://URL.com/...' of the source file
        file = file.split("/").slice(3).join("/");
        
        // Remove the beginning 'Uncaught Error: ' from the error message.
        // Since we ended up here we already know that the error was uncaught.
        message = message.split(" ").slice(2).join(" ");

        Storage.store.dispatch(
            Storage.messagesActions.addMessage(
                "exception",
                error.name + " in " + file + " on line " + line,
                message
            )
        );

        return false;
    };

    ServerConnection.initialize();
}

export function App() {
    return (
        <ThemeProvider theme={theme}>
            <Router>
                <Redirect exact from="/" to="/Main" />
                <Switch>
                    <Route path="/Main">
                        <Main />
                    </Route>
                    <Route path="/StartUp">
                        <StartUp />
                    </Route>
                </Switch>
            </Router>
        </ThemeProvider>
    )
}

export default App;

/**
 * Tab styled drawer for settings.
 */

import React, {useState} from 'react';
import { makeStyles } from '@material-ui/core/styles';
import TabDrawer from './TabDrawer.js';
import TabDrawerTab from './TabDrawerTab.js';
import ListItem from '@material-ui/core/ListItem';
import {Button} from '@material-ui/core';
import {Dialog, DialogActions, DialogTitle, DialogContent} from '@material-ui/core';
import {Navigate} from "react-router-dom";
import ModeButtonGroup from './ModeButtonGroup.js'
import SensorModeButtonGroup from './SensorModeButtonGroup.js'
import UndoIcon from '@material-ui/icons/Undo';
import { connect, areaWaypoints, areaWaypointActions, requestQueueActions, mapState, mapStateActions, activePicturesActions } from '../Storage.js';
import ModeIcon from './ModeIcon.js'
import ColorWrapper from '../ColorWrapper.js';

const useStyles = makeStyles( (theme) => ({
    fullWidthButton : {
        flexGrow: 1,
        justifyContent: 'center'
    }
}));

function SettingsDrawer(props) {

    const classes = useStyles();
    
    var [dialogOpen, setDialogState] = useState(false);
    var [redirected, redirect] = useState(false);
    redirect = redirect.bind(true);

    /**
     * Clickhandler for redefine button pressed. Opens dialog window.
     */
    function redefineClickHandler() {
        setDialogState(true);
    }

    /**
     * Clickhandler for confirmed dialog window. Reroutes to StartUp.
     */
    function reroute() {
        setDialogState(false);

        props.store.clearActivePictures();
        props.store.setMapState("StartUp");
        redirect(true);
    }

    return (
        <div>
        {redirected ? <Navigate to="/StartUp" /> : <div />}

        <TabDrawer
            anchor='left'
        >
            <TabDrawerTab 
                icon={<ModeIcon />} 
            >
                <ListItem>
                    <ModeButtonGroup />
                </ListItem>
                <ListItem>
                    <SensorModeButtonGroup />
                </ListItem>
                < div style={{flexGrow: 1}} />
                <ListItem>
                    <ColorWrapper
                        color="decline"
                    >
                        <Button
                            className={classes.fullWidthButton}
                            variant="contained" 
                            onClick={redefineClickHandler}
                            startIcon={<UndoIcon />}
                        >
                            Redefine area
                        </Button>
                    </ColorWrapper>
                </ListItem>
            </TabDrawerTab>
        </TabDrawer>

        <Dialog open={dialogOpen} onClose={() => {setDialogState(false)}}>
            <DialogTitle>
                Confirm redefining area of interest.
            </DialogTitle>
            <DialogContent>
                Are you sure you want to redefine the area of interest?
            </DialogContent>
            <DialogActions>
                <ColorWrapper
                    color="decline"
                >
                    <Button 
                        onClick={() => {setDialogState(false)}}
                        color="secondary"
                    >
                        Cancel
                    </Button>
                </ColorWrapper>
                <ColorWrapper
                    color="accept"
                >
                    <Button
                        onClick={reroute}
                    >
                        Confirm
                    </Button>
                </ColorWrapper>
            </DialogActions>
        </Dialog>
        </div>
    );
}

export default connect({areaWaypoints, mapState},{...areaWaypointActions, ...mapStateActions, ...requestQueueActions, ...activePicturesActions})( SettingsDrawer )

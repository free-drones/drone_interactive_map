/**
 * Initializes the app through the start-up sequence.
 */
import React, { useState, useEffect } from 'react';
import IMM_MAP from "../IMMMap.js";
import Axis from 'axis.js';
import clsx from 'clsx';

import Leaflet from 'leaflet';

import {Button, Fab} from '@mui/material';
import {Dialog, DialogActions, DialogTitle, DialogContent} from '@mui/material';
import {Navigate} from "react-router-dom";
import {connect, areaWaypointActions, areaWaypoints, mapBounds, mapBoundsActions, mapPosition, zoomLevel, mapPositionActions, mapState, mapStateActions, clientID, clientIDActions, messages} from "../Storage.js";
import { AttentionBorder, IncorrectAreaPopup } from "./AttentionBorder.js";
import {Check, Delete} from '@mui/icons-material';

import Downstream from '../Connection/Downstream.js';

import Snackbar from '@mui/material/Snackbar';
import { Alert } from '@mui/material';
import ClickAwayListener from '@mui/material/ClickAwayListener';
import ColorWrapper from '../ColorWrapper.js';

/**
 * Elevation of alert snackbars.
 */
const ALERT_ELEVATION = 6

function Alerter(props) {
  return <Alert elevation={ALERT_ELEVATION} variant="filled" {...props} />;
}

const styles = {
    fab: {
        position: 'absolute',
        bottom: (theme) => theme.spacing(3),
        zIndex: 'appBar'
    },
    fabRight: {
        right: (theme) => theme.spacing(3),
    },
    fabLeft: {
        left: (theme) => theme.spacing(3)
    },
    extendingFab: {
        // Medium button height
        height: (theme) => theme.spacing(7),
        borderRadius: (theme) => theme.spacing(7),
        justifyContent: 'flex-start',
        
        overflowX: 'hidden',
        paddingLeft: (theme) => theme.spacing(2),

        transition: (theme) => theme.transitions.create('all', {
            easing: 'easeOut',
            duration: 'standard',
        })
    }
};

/*
    This function loads component through its return function.
*/
function StartUp(props) {

    var [redirected, redirect] = useState(false);
    redirect = redirect.bind(true);

    var [dialogOpen, setDialogState] = useState(false);

    var [clearWaypointsConfirm, setClearwaypointsConfirm] = useState(false);

    var [snackbar, setSnackbar] = useState({
        open : false,
        severity : "",
        message : ""
    });

    useEffect(() => {
        const newMessage = props.store.messages[props.store.messages.length - 1]
        if (newMessage) {
            setSnackbar({
                open : true,
                severity : (newMessage.type === "message") ? "info" : "warning",
                message : newMessage.message
            });
        }
    }, [props.store.messages]);

    /**
     * Activates confirmation of clearing waypoints.
     */
    function toggleClearwaypointsConfirm() {
        setClearwaypointsConfirm(!clearWaypointsConfirm);
    }

    /**
     * Clears waypoints. 
     */
    function clearWaypoints() {
        props.store.clearAreaWaypoints();
    }

    /**
     * Creates a pair of coordinates from defined area to be used as bounds. 
     */
    function calculateBounds() {
        let bounds = Leaflet.latLngBounds(props.store.areaWaypoints)

        let topLeft = [bounds.getNorth(), bounds.getWest()]
        let bottomRight = [bounds.getSouth(), bounds.getEast()]

        return [topLeft, bottomRight];
    }

    /**
     * Clickhandler for when area is confirmed. Sets needed states and reroutes to main.
     */
    function defineArea() {
        
        const setArea = (clientID, areaWaypoints) => Downstream.setArea(clientID, areaWaypoints, Downstream.callbackWrapper((reply) => {
            setDialogState(false);

            let bounds = calculateBounds();
            props.store.setMapBounds(bounds);
            props.store.setMapState("Main");
            redirect(true);
        }));

        if (!Axis.isNumber(props.store.clientID))
            Downstream.connect(Downstream.callbackWrapper((reply) => {
                props.store.setClientID(reply.arg.client_id);
                setArea(reply.arg.client_id, props.store.areaWaypoints);
            }));
        else {
            setArea(props.store.clientID, props.store.areaWaypoints);
        }
    }

    return (
        
        <div>
            {redirected ? <Navigate to="/Main" /> : <div />}
            
            <ColorWrapper
                color="accept"
            >
                <Fab
                    onClick={() => {setDialogState(true)}}
                    sx={[styles.fab, styles.fabRight]}
                    disabled={(props.store.areaWaypoints.length<3)}
                >
                    <Check />
                </Fab>
            </ColorWrapper>

            <ClickAwayListener onClickAway={() => setClearwaypointsConfirm(false)}>
                <ColorWrapper
                    color="decline"
                >
                    <Fab
                        onClick={() => {
                                toggleClearwaypointsConfirm();
                                if (clearWaypointsConfirm)
                                    clearWaypoints();
                            }
                        }
                        variant={clearWaypointsConfirm ? "extended" : "round"}
                        sx={[styles.fab, styles.fabLeft, styles.extendingFab]}
                    >
                        <Delete />
                        {clearWaypointsConfirm ? 'Are you sure?' : ''}
                    </Fab>
                </ColorWrapper>
            </ClickAwayListener>
            
            <Snackbar open={snackbar.open} autoHideDuration={5000} onClose={() => setSnackbar({...snackbar, open : false})}>
                <Alerter onClose={() => setSnackbar({...snackbar, open : false})} severity={snackbar.severity}>
                    {snackbar.message}
                </Alerter>
            </Snackbar>

            <Dialog open={dialogOpen} onClose={() => {setDialogState(false)}}>
                <DialogTitle>
                    Confirm Area of Interest
                </DialogTitle>
                <DialogContent>
                    Confirm your area of interest. This can be reset later.
                </DialogContent>
                <DialogActions>
                    <ColorWrapper
                        color="decline"
                    >
                        <Button 
                            onClick={() => {setDialogState(false)}}
                        >
                            Cancel
                        </Button>
                    </ColorWrapper>
                    <ColorWrapper
                        color="accept"
                    >
                        <Button
                            onClick={defineArea}
                        >
                            Confirm
                        </Button>
                    </ColorWrapper>
                </DialogActions>
            </Dialog>

            <AttentionBorder>
                DEFINE AREA
            </AttentionBorder>

            <IncorrectAreaPopup>
                TEST
            </IncorrectAreaPopup>

            <IMM_MAP center={props.store.mapPosition.center} zoom={props.store.zoomLevel} allowDefine={true} />
        </div>
    );
}

export default connect({ areaWaypoints, mapBounds, mapPosition, zoomLevel, mapState, clientID, messages },{ ...areaWaypointActions, ...mapBoundsActions, ...mapPositionActions, ...mapStateActions, ...clientIDActions })(StartUp)

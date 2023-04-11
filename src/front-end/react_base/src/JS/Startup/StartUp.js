/**
 * Initializes the app through the start-up sequence.
 */
import React, { useState, useEffect, useRef } from 'react';
import IMM_MAP from "../IMMMap.js";
import Axis from 'axis.js';
import clsx from 'clsx';

import Leaflet from 'leaflet';

import {Button, Fab} from '@mui/material';
import {Dialog, DialogActions, DialogTitle, DialogContent} from '@mui/material';
import {Navigate} from "react-router-dom";
import {connect, config, setConfigValue, areaWaypointActions, areaWaypoints, mapBounds, mapBoundsActions, mapPosition, zoomLevel, mapPositionActions, mapState, mapStateActions, clientID, clientIDActions, messages, configActions, showWarning, showWarningActions} from "../Storage.js";
import { AttentionBorder } from "./AttentionBorder.js";
import {Check, Delete, MyLocation} from '@mui/icons-material';

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
    },
    fabAbove: {
        bottom: (theme) => theme.spacing(14)
    },
    hidden: {
        visibility: "hidden"
    }
};

/*
    This function loads component through its return function.
*/
function StartUp(props) {

    let [redirected, redirect] = useState(false);
    redirect = redirect.bind(true);

    let [dialogOpen, setDialogState] = useState(false);

    let [clearWaypointsConfirm, setClearwaypointsConfirm] = useState(false);

    let [snackbar, setSnackbar] = useState({
        open : false,
        severity : "",
        message : ""
    });

    // showWarning is bool for if to show crossing lines warning
    let showWarning = props.store.showWarning;
    const centerButton = useRef();

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
        props.store.setShowWarning(false);
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
                    onClick={() => {
                        setDialogState(true);
                        props.store.setShowWarning(false);
                    }}
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


            <ColorWrapper
                ref={centerButton}
                color="#CDCDCD"
            >
                <Fab
                    sx={[styles.fab, styles.fabRight, styles.fabAbove, styles.hidden]}
                >
                    <MyLocation />
                </Fab>
            </ColorWrapper>


            <AttentionBorder>
                DEFINE AREA
            </AttentionBorder>

            <div>
                <Snackbar
                    open={showWarning}
                    autoHideDuration={3000}
                    onClose={() => props.store.setShowWarning(false)}
                    message="Warning: Lines are not allowed to cross"
                    anchorOrigin={{ 
                        vertical: 'top',
                        horizontal: 'center'
                    }}
                />
            </div>
 
            <IMM_MAP center={props.store.mapPosition.center} zoom={props.store.zoomLevel} allowDefine={true} centerButton={centerButton}/>
        </div>
    );
}
export default connect({ areaWaypoints, mapBounds, mapPosition, zoomLevel, mapState, clientID, config, messages, showWarning },{ ...areaWaypointActions, ...mapBoundsActions, ...mapPositionActions, ...mapStateActions, ...clientIDActions, ...configActions, ...showWarningActions })(StartUp)

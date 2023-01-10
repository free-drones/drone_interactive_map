/**
 * Class file for camera button component.
 */

import { Fab } from '@material-ui/core';
import AddAPhoto from '@material-ui/icons/AddAPhoto'
import React from 'react';

import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles( (theme) => ({
    cameraButton : {
        position: 'absolute',
        zIndex: theme.zIndex.appBar,

        bottom: theme.spacing(2),
        left: '50%',
        transform: "translate(-50%, 0)" //transform ensures position is in the middle
    }
}));

function CameraButton (props) {
    const classes = useStyles();

    return (
        //Creates a floating object, Fab
        <Fab className={classes.cameraButton} onClick={props.clickHandler}>
            <AddAPhoto />
        </Fab>
    );
}
export default CameraButton

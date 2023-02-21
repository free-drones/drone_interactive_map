/**
 * Class file for camera button component.
 */

import { Fab } from '@mui/material';
import AddAPhoto from '@mui/icons-material/AddAPhoto'
import React from 'react';

import { makeStyles } from '@mui/styles';

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

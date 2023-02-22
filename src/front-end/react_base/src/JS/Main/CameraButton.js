/**
 * Class file for camera button component.
 */

import { Fab } from '@mui/material';
import AddAPhoto from '@mui/icons-material/AddAPhoto'
import React from 'react';


const styles = {
    cameraButton : {
        position: 'absolute',
        zIndex: 'appBar',

        bottom: (theme) => theme.spacing(2),
        left: '50%',
        transform: "translate(-50%, 0)" //transform ensures position is in the middle
    }
};

function CameraButton (props) {

    return (
        //Creates a floating object, Fab
        <Fab sx={styles.cameraButton} onClick={props.clickHandler}>
            <AddAPhoto />
        </Fab>
    );
}
export default CameraButton

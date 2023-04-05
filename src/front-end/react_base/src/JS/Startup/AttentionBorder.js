/**
 * AttentionBorder component. Screen wide border for especially attention-needing tasks, like defining area of intrest.
 */

import React from 'react';

import Typography from '@mui/material/Typography';
import { Box } from '@mui/system';

const styles = {
    borderBox: {
        position: 'absolute',
        
        overflow: 'hidden',

        height: (theme) => `calc(100% - ${theme.spacing(4)})`,
        width:  (theme) => `calc(100% - ${theme.spacing(4)})`,

        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",

        borderColor: 'error.main',
        borderStyle: "dashed",
        borderWidth: (theme) => theme.spacing(1),
        borderRadius: (theme) => theme.spacing(1),

        pointerEvents: 'none',

        zIndex: 'appBar'
    },
    borderHead: {
        position: 'absolute',

        top: (theme) => theme.spacing(3),
        left: "50%",
        transform: "translate(-50%, 0)",
        
        padding: (theme) => theme.spacing(1),
        color: 'error.main',
        boxShadow: (theme) => theme.shadows[5],
        borderRadius: (theme) => theme.spacing(1),
        backgroundColor: "rgba(255,255,255,0.75)",

        zIndex: (theme) => theme.zIndex.appBar - 1,
        pointerEvents: 'none',

        ...((theme) => theme.typography.button)
    },

    borderCenter: {
        position: 'absolute',
        top: "13%",
        left: "50%",
        transform: "translate(-50%, 0)",
        
        padding: (theme) => theme.spacing(1),
        //color: 'error.main',
        boxShadow: (theme) => theme.shadows[5],
        borderRadius: (theme) => theme.spacing(1),
        backgroundColor: "rgba(255,255,255,0.75)",

        zIndex: (theme) => theme.zIndex.appBar - 1,
        pointerEvents: 'none',

        ...((theme) => theme.typography.button)
    }
    
};


/**
 * AttentionBorder component function.
 */
export function AttentionBorder(props) {

    return (
        <div>
            <Box
                sx={styles.borderHead}
            >
                <Typography variant="h6" component="h2" elevation={10}>
                    {props.children}
                </Typography>
            </Box>
            <Box sx={styles.borderBox}/>
        </div>
    );
}

/**
 * IncorrectAreaPopup component function.
 */
export function IncorrectAreaPopup(props) {

    return (
        <div>
            <Box
                sx={styles.borderCenter}
            >
                <Typography variant="h4" component="h2" elevation={10}>
                    {props.children}
                </Typography>
            </Box>
            <Box sx={styles.borderBox}/>
            
        </div>
    );
}
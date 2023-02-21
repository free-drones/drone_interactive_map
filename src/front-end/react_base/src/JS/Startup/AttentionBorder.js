/**
 * AttentionBorder component. Screen wide border for especially attention-needing tasks, like defining area of intrest.
 */

import React from 'react';
import { makeStyles } from '@mui/styles';

import Typography from '@mui/material/Typography';

const useStyles = makeStyles((theme) => ({
    borderBox: {
        position: 'absolute',
        
        overflow: 'hidden',

        height: `calc(100% - ${theme.spacing(4)})`,
        width:  `calc(100% - ${theme.spacing(4)})`,

        top: "50%",
        left: "50%",
        transform: "translate(-50%, -50%)",

        borderColor: theme.palette.error.main,
        borderStyle: "dashed",
        borderWidth: theme.spacing(1),
        borderRadius: theme.spacing(1),

        pointerEvents: 'none',

        zIndex: theme.zIndex.appBar
    },
    borderHead: {
        position: 'absolute',

        top: theme.spacing(3),
        left: "50%",
        transform: "translate(-50%, 0)",
        
        padding: theme.spacing(1),
        color: theme.palette.error.main,
        boxShadow: theme.shadows[5],
        borderRadius: theme.spacing(1),
        backgroundColor: "rgba(255,255,255,0.75)",

        zIndex: theme.zIndex.appBar - 1,
        pointerEvents: 'none',

        ...theme.typography.button
    }
}));


/**
 * AttentionBorder component function.
 */
export function AttentionBorder(props) {
    
    const classes = useStyles(props);

    return (
        <div>
            <div
                className={classes.borderHead}
            >
                <Typography variant="h6" component="h2" elevation={10}>
                    {props.children}
                </Typography>
            </div>
            <div className={classes.borderBox}/>
        </div>
    );
}
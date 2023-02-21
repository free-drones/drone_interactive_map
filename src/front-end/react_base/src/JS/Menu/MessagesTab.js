/**
 * Tab drawer tab for messages.
 */

import React from 'react';
import { useState } from 'react';
import { makeStyles } from '@mui/styles';

import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemIcon from '@mui/material/ListItemIcon';

import Divider from '@mui/material/Divider';

import Button from '@mui/material/Button';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Checkbox from '@mui/material/Checkbox';

import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import FilterListIcon from '@mui/icons-material/FilterList';
import FlashOnIcon from '@mui/icons-material/FlashOn';
import ErrorIcon from '@mui/icons-material/Error';

import { MESSAGE_TYPES, connect, messages, messagesActions } from '../Storage.js';
import ColorWrapper from '../ColorWrapper.js';

const useStyles = makeStyles( (theme) => ({
    fullWidthButton : {
        flexGrow: 1,
        justifyContent: 'center'
    },
    thinIcon : {
        minWidth: theme.spacing(2),
        alignSelf: 'flex-start'
    },
    wrappingText : {
        whiteSpace: "normal",
        textAlign: 'justify',
        textJustify: 'inter-word',
        margin: 0
    }
}));

function MessagesTab(props) {
    const classes = useStyles();
    
    const [menuAnchor, setMenuAnchor] = React.useState(null);
    const [menuOpen, setMenuOpen] = React.useState(false);

    /*
        Set default state to:
        {
            error: true
            exception: true
            message: true
        }
    */
    var [filter, setFilter] = useState(Object.fromEntries(MESSAGE_TYPES.map((filterKey) => {return [filterKey, true]})));

    /**
     * Toggle the state of a given filter.
     * 
     * @param {String} filterKey Filter to toggle
     */
    function toggleFilter(filterKey) {
        setFilter({
            ...filter,
            [filterKey]: !filter[filterKey]
        });
    }
    
    /**
     * Handle menu button being clicked. This opens the menu.
     */
    function menuButtonClick(e) {
        setMenuAnchor(e.currentTarget);
        setMenuOpen(!menuOpen)
    }

    /**
     * Get an appropriate icon for a given message type.
     * 
     * @param {String} type Message type
     */
    function getIconByType(type) {
        switch(type){
            case "error":
                return <ErrorIcon />
            case "exception":
                return <FlashOnIcon />
            case "message":
                return <ChevronRightIcon />
            default:
                return <div/>
        }
    }

    return (
        <div>
            <Menu
                keepMounted
                open={menuOpen}
                onClose={() => setMenuOpen(false)}
                getContentAnchorEl={null}
                anchorEl={menuAnchor}
                anchorOrigin={{
                    vertical: 'bottom',
                    horizontal: 'center'
                }}
                transformOrigin={{
                    vertical: 'top',
                    horizontal: 'center'
                }}
            >
                {/* Add all filter options to the menu with togglable buttons. */}
                {MESSAGE_TYPES.map((filterKey) => 
                    <MenuItem key={filterKey} value={filterKey} onClick={() => toggleFilter(filterKey)}>
                        <Checkbox checked={filter[filterKey] === true} />
                        <ListItemText primary={filterKey.toUpperCase() + "S"} />
                    </MenuItem>
                )}
            </Menu>
            {/* Filter menu button */}
            <ListItem>
                <Button
                    color="primary"
                    onClick={menuButtonClick}
                    variant="contained"
                    endIcon={<FilterListIcon />}
                    className={classes.fullWidthButton}
                >
                    Filter
                </Button>
            </ListItem>
            {/* Clear messages button */}
            <ListItem>
                <ColorWrapper
                    color="decline"
                >
                    <Button
                        onClick={() => props.store.clearMessages()}
                        variant="contained"
                        className={classes.fullWidthButton}
                    >
                        Clear messages
                    </Button>
                </ColorWrapper>
            </ListItem>
            <Divider />
            <List>
            {/* First filter for relevant messages, then add all to list */}
            {props.store.messages.filter((message) => filter[message.type] === true).map((message) => 
                <ListItem>
                    <ListItemIcon className={classes.thinIcon}>
                        {getIconByType(message.type)}
                    </ListItemIcon>
                    <ListItemText className={classes.wrappingText} primary={message.heading} secondary={message.message}  />
                </ListItem>
            )}
            </List>
        </div>
    );
}

export default connect({ messages }, { ...messagesActions })(MessagesTab);
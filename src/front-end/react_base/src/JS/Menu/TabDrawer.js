/**
 * TabDrawer. Styled multi-drawer component with tab styled activation buttons.
 */

import React from 'react';
import { useState } from 'react';

import { makeStyles } from '@material-ui/core/styles';

import ClickAwayListener from '@material-ui/core/ClickAwayListener';
import Portal from '@material-ui/core/Portal';

const useStyles = makeStyles((theme) => ({
    // Page wrapper hides unwanted overflow from overextending tabs heads
    pageWrapper: {
        height: '100%',
        width: '100%',

        position: 'absolute',
        
        left: 0,
        top: 0,
        
        overflow: 'hidden',
        pointerEvents: 'none',

        zIndex: theme.zIndex.appBar,

        // Re-enable click events for all children
        '& > *': {
            pointerEvents: 'auto'
        }
    }
}));

/**
 * @typedef {Object} Properties
 * @property {String} anchor Side of screen to anchor to. Either 'left' or 'right'.
 * @property {Boolean} [persistent=false] If the drawer should automatically disappear.
 * @property {Object[]} children Child elements. Must be of type TabDrawerTab.
 */

/**
 * Tab drawer. Contains and maintains TabDrawerTabs. Automatically gives them indexes and states, as well as groups them together.
 * 
 * @param {Properties} props Passed properties.
 */
function TabDrawer(props) {
    const classes = useStyles(props)
    
    // Set up default states
    var [states, setStates] = useState(new Array(props.children.length).fill('dormant'));

    // Map correct props to all children
    const children = React.Children.map(props.children, (child, index) => 
        React.cloneElement(child, {
            index: index,
            anchor: props.anchor,
            state: states[index],
            tabHeadCallback: (newState) => tabHeadClicked(index, newState)
        })
    );

    /**
     * Handle tab clicked event. This callback method is passed to children as a prop bound to their corrensponding index.
     * 
     * @param {Number} index Intex of clicked tab
     * @param {String} newState New state of clicked tab
     */
    function tabHeadClicked(index, newState) {
        let newStates = Array(children.length);

        if (newState === 'dormant') {
            newStates.fill('dormant');
        }
        else if (newState === 'active') {
            newStates.fill('passive');
            newStates[index] = 'active';
        }

        setStates(newStates);
    }

    /**
     * Handle click away event. Automatically closes open drawers when another element is clicked.
     * Controlled by the 'persistent' property.
     */
    function handleClickAway() {
        if (!props.persistent) {
            setStates(new Array(children.length).fill('dormant'));
        }
    }

    return (
        <Portal>
            <ClickAwayListener onClickAway={handleClickAway}>
                <div className={classes.pageWrapper}>
                    { children }
                </div>
            </ClickAwayListener>
        </Portal>
    );
}

export default TabDrawer
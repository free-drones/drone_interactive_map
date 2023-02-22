/**
 * TabDraderTab component. Drawer with tab styled activation button.
 */

import React, { useState, useEffect } from 'react';

import Paper from '@mui/material/Paper';
import IconButton from '@mui/material/IconButton';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';

/**
 * Drawer width constant
 */
const DRAWER_WIDTH = 200;

/**
 * Tab head extention constant. Amount of extra width added to tab head.
 */
const TAB_HEAD_EXTENTION = 100;

/**
 * Inter tab padding constant. Specifies the horizontal padding between components.
 */
const TAB_HEAD_PADDING = 2;

/**
 * Tab head size. 36px (4dp) for medium button, 6px (1dp) for each side of padding.
 */
const TAB_HEAD_SIZE = 36 + (6 * 2) + TAB_HEAD_PADDING;


/**
 * @typedef {Object} Properties
 * @property {String} anchor Side of screen to anchor to. Either 'left' or 'right'.
 * @property {Icon} icon Tab head button icon.
 * @property {String} [state=dormant] Initial drawer state. Either 'active', 'passive' och 'dormant'.
 * @property {Object[]} children Child objects.
 */

/**
 * Tab drawer tab. Adds a drawer together with a tab styled activation button.
 * 
 * @param {Properties} props Passed properties.
 */
function TabDrawerTab(props) {

    // Inject default state
    var [state, setState] = useState(props.state || 'dormant');

    // Sync state with parent
    useEffect(() => {
        setState(props.state);
    }, [props.state]);

    /**
     * Handle tab head click event.
     */
    function tabHeadClick() {
        // Clicking an already active tab will make it dormant.
        if (state === 'active') {
            setState('dormant');
            props.tabHeadCallback('dormant');
        }
        // Clicking an inactive or dormant tab till make it active.
        else {
            setState('active');
            props.tabHeadCallback('active');
        }
    }

    /**
     * Elevation function. Returns appropriate tab head elevation for current state.
     */
    function elevation() {
        switch(state) {
            case 'active':
                return 5;
            case 'passive':
                return 2;
            case 'dormant':
                return 1;
            default:
                return 0;
        }
    }

    // The entire styling might need an overhaul, this is a temporary solution from the library update
    function getStyle(styleClass, props) {
        switch(styleClass) {
            case 'tabHead': 
                return {
                    // Make tab head paper wider than actual button, hiding the overflow neatly behind the drawer.
                    width: (TAB_HEAD_SIZE + TAB_HEAD_EXTENTION),

                    // Move tab head content (button) to appropriate side of button.
                    display: 'flex',
                    justifyContent: (props.anchor === 'left') ? 'flex-end' : 'flex-start',

                    position: 'absolute',
                    top: props.index * TAB_HEAD_SIZE,
                    // Offset button to hide one of the edges. Swap offset direction based in anchor direction.
                    transform: 'translate(' + (props.anchor === 'left' ? '-' : '') + TAB_HEAD_EXTENTION + 'px, 0)',
                    
                    // Match appbar z-index. Drawer har a higher z-index than app-bar by default.
                    zIndex: 'appbar'
                }
            case 'active': 
                return {
                    // Switch button side depending on anchor.
                    left: props.anchor === 'left' && DRAWER_WIDTH,
                    right: props.anchor === 'right' && DRAWER_WIDTH,
                    backgroundColor: 'primary'
                }
            case 'passive': 
                return {
                    // Switch button side depending on anchor.
                    // Offset passive tabs closer to the corresponding drawer.
                    left: props.anchor === 'left' && (DRAWER_WIDTH - TAB_HEAD_SIZE / 10),
                    right: props.anchor === 'right' && (DRAWER_WIDTH - TAB_HEAD_SIZE / 10),
                }
            case 'dormant': 
                return {
                    // Switch button side depending on anchor.
                    left: props.anchor === 'left' && 0,
                    right: props.anchor === 'right' && 0,
                }
            case 'drawer': 
                return {
                    // Make sure drawer is of correct size to line up with tab heads.
                    width: DRAWER_WIDTH,
                    minWidth: DRAWER_WIDTH,
                    flexGrow: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    whiteSpace: 'nowrap',
                    overflowX: 'hidden'
                }
            case 'drawerOpened': 
                return {
                    width: DRAWER_WIDTH,
                }
            case 'drawerClosed': 
                return {
                    width: '0'
                }
            case 'openAnimation': 
                return {
                        // Match transition to drawers Slide object animation.
                        transition: (theme) => theme.transitions.create(['width', 'left', 'right'], {
                        easing: 'easeOut',
                        duration: 'enteringScreen',
                    })
                }
            case 'closeAnimation': 
                return {
                        // Match transition to drawers Slide object animation.
                        transition: (theme) => theme.transitions.create(['width', 'left', 'right'], {
                        easing: 'sharp',
                        duration: 'leavingScreen',
                    })
                }
            default:
                return {}
        }
    };

    return (
        <div>
            {/* Tab head */}
            <Paper
                // The entire styling might need an overhaul, this is a temporary solution from the library update
                sx={[getStyle('tabHead', props),
                    getStyle(state, props),
                    (state === 'active' || state === 'passive') ? getStyle("openAnimation", props) : {},
                    (state === 'dormant') ? getStyle("closeAnimation", props) : {}
                ]}
                elevation={elevation()}
            >
                <IconButton onClick={tabHeadClick} size='medium'>
                    { props.icon }
                </IconButton>
            </Paper>
            
            {/* Tab content */}
            <Drawer
                variant="persistent"
                elevation={5}
                anchor={props.anchor}
                open={(state === 'active')}
                // The entire styling might need an overhaul, this is a temporary solution from the library update
                sx={[
                    getStyle('drawer', props),
                    (state === 'active' || state === 'passive') ? getStyle("openAnimation", props) : {},
                    (state === 'dormant') ? getStyle("closeAnimation", props) : {},
                    (state === 'active' || state === 'passive') ? getStyle("drawerOpened", props) : {},
                    (state === 'dormant') ? getStyle("drawerClosed", props) : {}
                ]}
            >
                {/* Make sure tab has correct width*/}
                <List
                    // The entire styling might need an overhaul, this is a temporary solution from the library update
                    sx={getStyle('drawer')}
                >
                    {/* Add tab content*/}
                    { props.children }
                </List>
            </Drawer>
        </div>
    );
}

export default TabDrawerTab
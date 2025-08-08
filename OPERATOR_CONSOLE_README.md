# Operator Console Layout & Hotspots

## Overview
This is a performance-first operator control panel designed for high-density information display and instant control feedback. The interface is built for mechanical-engineer grade precision with minimal visual fluff.

## Layout Structure

### 1. Fixed Top Status & Control Strip (Always Visible)
**Position**: Fixed at top, never scrolls out of view
**Height**: ~60px
**Components**:
- **Mode Toggle**: Yellow (Safe Mode) / Green (Live Mode) with clear state labels
- **System Control**: Primary Start/Stop button with high contrast
- **Critical Metrics**: Auto-refresh every 3 seconds
  - Uptime (hours)
  - Success Rate (%)
  - Tasks/hour
  - Active Devices count
  - Average Response time (ms)
- **Alerts Icon**: Blinks red when errors detected

### 2. Main Control Zone (Two Columns)
**Position**: Below top strip, main content area
**Layout**: Side-by-side on desktop, stacked on mobile

#### Left Column - Device Control & Monitoring
- **Compact Device Table**: Shows all connected devices
  - Columns: Device | Status | Mode | Response | Queue | Actions
  - Inline row actions: Toggle Safe/Live, Refresh
  - Color coding: Green (good), Yellow (caution), Red (critical)
- **FallbackBanner**: Only visible when devices are offline/rate-limited

#### Right Column - Task & Workflow Management  
- **Quick Actions Panel**: 
  - CREATE TASK button (blue)
  - CREATE WORKFLOW button (purple)
- **Task Queue Table**: Recent 5 tasks with ETA and device assignment
- **Workflow Overview**: Active workflows with progress indicators

### 3. Bottom Strip - Logs & Advanced Tools
**Position**: Fixed at bottom, tabbed interface
**Height**: 256px (1/4 of screen)
**Tabs**:
- **System Log**: Real-time log tail with filtering
- **Interaction Log**: Instagram action history
- **Mode Settings**: Full ModeToggle component
- **Settings**: System configuration

## Key Features

### Performance Optimizations
- **Real-time Updates**: Metrics refresh every 3s, logs every 5s
- **Minimal Re-renders**: State managed to prevent unnecessary updates
- **Instant Feedback**: All actions show immediate toast notifications
- **High-density Tables**: Compact rows with maximum information

### Accessibility & Usability
- **No Hidden Actions**: All core controls visible without extra clicks
- **Keyboard Navigation**: Full tab support maintained
- **Color-coded Status**: Consistent color meaning throughout
- **Responsive Design**: Mobile-friendly with critical controls preserved

### Safety Features
- **Mode Awareness**: Clear Safe/Live mode indication at all times
- **Confirmation Dialogs**: Live mode operations require explicit confirmation
- **Fallback Notifications**: Immediate alerts when devices go offline
- **Audit Trail**: All actions logged with timestamps

## Hotspots & Quick Actions

### Primary Controls (Top Strip)
1. **Mode Toggle**: Click to switch Safe ↔ Live mode
2. **START/STOP**: Primary system control
3. **Metrics**: Click metrics for detailed view
4. **Alerts**: Click to open alert log

### Device Management (Left Panel)
1. **TOGGLE**: Switch individual device Safe/Live mode
2. **Refresh**: Force device status update
3. **Status Colors**: Visual device health at a glance

### Task Operations (Right Panel)
1. **CREATE TASK**: Opens task wizard (2 clicks to create)
2. **CREATE WORKFLOW**: Opens workflow wizard (2 clicks to create)
3. **Queue Items**: Click task for details

### Advanced Tools (Bottom Strip)
1. **System Log**: Live tail with level filtering
2. **Mode Settings**: Advanced dual-mode configuration
3. **Settings**: System-wide preferences

## Technical Implementation

### State Management
- Real-time metrics via interval updates
- Efficient device status caching
- Optimistic UI updates for better UX

### API Integration
- All Phase 4 Live Device Integration endpoints supported
- Automatic fallback handling
- Comprehensive error handling

### Mobile Responsiveness
- Top strip becomes two rows on small screens
- Two-column layout stacks vertically
- Critical controls always visible
- Touch-friendly button sizes

## Color Coding System
- **Green**: Active, healthy, success states
- **Yellow**: Caution, safe mode, warnings
- **Red**: Errors, stop actions, critical states
- **Blue**: Actions, information, neutral operations
- **Gray**: Inactive, disabled, secondary information

## Performance Targets
- **Initial Load**: < 2 seconds
- **Action Feedback**: < 200ms
- **Metrics Update**: 3 second intervals
- **Log Streaming**: 5 second intervals
- **Memory Usage**: Optimized for 24/7 operation
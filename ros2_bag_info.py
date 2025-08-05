#!/usr/bin/env python3
"""
Nautilus extension to show ROS2 bag metadata in submenus
Save this file as: ~/.local/share/nautilus-python/extensions/ros2_bag_info.py
"""

import os
import yaml
from urllib.parse import unquote
from datetime import datetime, timezone
import gi
gi.require_version('Nautilus', '4.0')
from gi.repository import Nautilus, GObject

class ROS2BagInfoExtension(GObject.GObject, Nautilus.MenuProvider):
    
    def __init__(self):
        super().__init__()
        self._cache = {}  # Cache for bag summaries
    
    def get_file_items(self, files):
        """Add menu items for ROS2 bag files"""
        try:
            if len(files) != 1:
                return []
            
            file_info = files[0]
            file_uri = file_info.get_uri()
            file_path = unquote(file_uri.replace('file://', ''))
            
            # Quick check if it's a ROS2 bag directory
            if os.path.isdir(file_path):
                metadata_path = os.path.join(file_path, 'metadata.yaml')
                
                is_ros2_bag = False
                if os.path.exists(metadata_path):
                    # Check for .mcap or .db3 files in the directory
                    try:
                        for filename in os.listdir(file_path):
                            if filename.endswith('.mcap') or filename.endswith('.db3'):
                                is_ros2_bag = True
                                break
                    except OSError:
                        pass
                
                if is_ros2_bag:
                    return self._create_info_submenu(file_path, metadata_path)
            
            return []
            
        except Exception:
            return []
    
    def _create_info_submenu(self, file_path, metadata_path):
        """Create a submenu with bag information"""
        try:
            # Check cache first
            cache_key = f"{metadata_path}:{os.path.getmtime(metadata_path)}"
            if cache_key in self._cache:
                bag_summary = self._cache[cache_key]
            else:
                # Parse metadata and cache it
                bag_summary = self._get_bag_summary(metadata_path)
                self._cache[cache_key] = bag_summary
                # Limit cache size
                if len(self._cache) > 50:
                    oldest_keys = list(self._cache.keys())[:10]
                    for key in oldest_keys:
                        del self._cache[key]
            
            # Create main menu item
            main_item = Nautilus.MenuItem(
                name="ROS2BagInfo::bag_info",
                label=f"ROS2 Bag Info",
                tip=f"View information about {os.path.basename(file_path)}",
                icon="dialog-information"
            )
            
            # Create submenu
            submenu = Nautilus.Menu()
            main_item.set_submenu(submenu)
            
            # Start Time
            submenu.append_item(Nautilus.MenuItem(
                name="ROS2BagInfo::start_time",
                label=f"Start: {bag_summary['start_time']}",
                tip=f"Recording start time: {bag_summary['start_time']}"
            ))
            
            # End Time
            submenu.append_item(Nautilus.MenuItem(
                name="ROS2BagInfo::end_time",
                label=f"End: {bag_summary['end_time']}",
                tip=f"Recording end time: {bag_summary['end_time']}"
            ))
            
            # Duration
            submenu.append_item(Nautilus.MenuItem(
                name="ROS2BagInfo::duration",
                label=f"Duration: {bag_summary['duration']}",
                tip=f"Recording duration: {bag_summary['duration']}"
            ))
            
            # Size
            submenu.append_item(Nautilus.MenuItem(
                name="ROS2BagInfo::size",
                label=f"Size: {bag_summary['size']}",
                tip=f"Bag file size: {bag_summary['size']}"
            ))
            
            # Messages
            submenu.append_item(Nautilus.MenuItem(
                name="ROS2BagInfo::messages",
                label=f"Messages: {bag_summary['message_count']}",
                tip=f"Total messages: {bag_summary['message_count']}"
            ))
            
            # Topics with submenu
            topics_item = Nautilus.MenuItem(
                name="ROS2BagInfo::topics",
                label=f"Topics: {bag_summary['topic_count']}",
                tip=f"Number of topics: {bag_summary['topic_count']}"
            )
            
            # Create topics submenu if there are topics
            if bag_summary['topics'] and len(bag_summary['topics']) > 0:
                topics_submenu = Nautilus.Menu()
                topics_item.set_submenu(topics_submenu)
                
                for topic_info in bag_summary['topics']:
                    topic_menu_item = Nautilus.MenuItem(
                        name=f"ROS2BagInfo::topic_{topic_info['name'].replace('/', '_')}",
                        label=f"{topic_info['name']}: {topic_info['count']}",
                        tip=f"Topic: {topic_info['name']} | Type: {topic_info['type']} | Messages: {topic_info['count']}"
                    )
                    topics_submenu.append_item(topic_menu_item)
            
            submenu.append_item(topics_item)
            
            # View Metadata option
            metadata_item = Nautilus.MenuItem(
                name="ROS2BagInfo::view_metadata",
                label="View Metadata",
                tip="View the raw metadata.yaml file content"
            )
            metadata_item.connect("activate", self._view_metadata_file, file_path)
            submenu.append_item(metadata_item)
            
            return [main_item]
            
        except Exception:
            return []
    
    def _get_bag_summary(self, metadata_path):
        """Get summary of bag information from metadata.yaml"""
        try:
            with open(metadata_path, 'r') as f:
                data = yaml.safe_load(f)
            
            bag_info = data.get('rosbag2_bagfile_information', {})
            
            # Duration
            duration_ns = bag_info.get('duration', {}).get('nanoseconds', 0)
            duration_s = duration_ns / 1e9
            if duration_s >= 3600:
                duration_str = f"{int(duration_s//3600)}h {int((duration_s%3600)//60)}m"
            elif duration_s >= 60:
                duration_str = f"{int(duration_s//60)}m {int(duration_s%60)}s"
            else:
                duration_str = f"{duration_s:.1f}s"
            
            # Start/End time
            start_time_ns = bag_info.get('starting_time', {}).get('nanoseconds_since_epoch', 0)
            if start_time_ns:
                start_dt = datetime.fromtimestamp(start_time_ns / 1e9, tz=timezone.utc)
                start_time_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
                if duration_ns:
                    end_dt = datetime.fromtimestamp((start_time_ns + duration_ns) / 1e9, tz=timezone.utc)
                    end_time_str = end_dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    end_time_str = 'unknown'
            else:
                start_time_str = end_time_str = 'unknown'
            
            # Messages and topics
            message_count = bag_info.get('message_count', 0)
            topics_data = bag_info.get('topics_with_message_count', [])
            topic_count = len(topics_data)
            
            # Build topics list
            topics_list = []
            for topic in topics_data:
                topic_meta = topic.get('topic_metadata', {})
                topics_list.append({
                    'name': topic_meta.get('name', 'unknown'),
                    'type': topic_meta.get('type', 'unknown'),
                    'count': topic.get('message_count', 0)
                })
            topics_list.sort(key=lambda x: x['name'])
            
            # Size calculation
            size_str = self._calculate_bag_size(metadata_path, bag_info)
            
            return {
                'duration': duration_str,
                'start_time': start_time_str,
                'end_time': end_time_str,
                'message_count': message_count,
                'topic_count': topic_count,
                'topics': topics_list,
                'size': size_str
            }
            
        except Exception:
            return {
                'duration': 'unknown',
                'start_time': 'unknown', 
                'end_time': 'unknown',
                'message_count': 'unknown',
                'topic_count': 'unknown',
                'topics': [],
                'size': 'unknown'
            }
    
    def _calculate_bag_size(self, metadata_path, bag_info):
        """Calculate total bag size"""
        try:
            file_paths = bag_info.get('relative_file_paths', [])
            if not file_paths:
                return 'unknown'
            
            bag_dir = os.path.dirname(metadata_path)
            total_size = 0
            for file_path in file_paths:
                full_path = os.path.join(bag_dir, file_path)
                try:
                    total_size += os.path.getsize(full_path)
                except OSError:
                    continue
            
            return self._format_bytes(total_size)
        except Exception:
            return 'unknown'
    
    def _format_bytes(self, bytes_size):
        """Format bytes in human readable format"""
        if bytes_size == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                if unit == 'B':
                    return f"{int(bytes_size)} {unit}"
                else:
                    return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
    
    def _view_metadata_file(self, menu_item, file_path):
        """Open the metadata.yaml file in the default text editor"""
        metadata_path = os.path.join(file_path, 'metadata.yaml')
        if os.path.exists(metadata_path):
            os.system(f'xdg-open "{metadata_path}"')
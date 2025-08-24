from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging

logger = logging.getLogger(__name__)

class IPBlocker:
    def __init__(self):
        self.blocked_ips = {}  # ip -> {reason, blocked_until, level}
        self.block_levels = {
            'temporary': timedelta(minutes=30),
            'extended': timedelta(hours=6),
            'permanent': None
        }
    
    def block_ip(self, ip: str, reason: str, level: str = 'temporary') -> bool:
        """Block an IP address"""
        if level not in self.block_levels:
            logger.error(f"Invalid block level: {level}")
            return False
        
        blocked_until = None
        if self.block_levels[level]:
            blocked_until = datetime.utcnow() + self.block_levels[level]
        
        self.blocked_ips[ip] = {
            'reason': reason,
            'blocked_until': blocked_until,
            'level': level,
            'blocked_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Blocked IP {ip} with level {level}: {reason}")
        return True
    
    def is_blocked(self, ip: str) -> Optional[Dict]:
        """Check if IP is blocked"""
        if ip not in self.blocked_ips:
            return None
        
        block_info = self.blocked_ips[ip]
        
        # Check if temporary block has expired
        if block_info['blocked_until'] and datetime.utcnow() > block_info['blocked_until']:
            del self.blocked_ips[ip]
            logger.info(f"IP {ip} block expired, unblocked automatically")
            return None
        
        return block_info
    
    def unblock_ip(self, ip: str) -> bool:
        """Unblock an IP address"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            logger.info(f"Manually unblocked IP {ip}")
            return True
        return False
    
    def get_blocked_ips(self) -> Dict[str, Dict]:
        """Get all currently blocked IPs"""
        # Clean expired blocks
        current_time = datetime.utcnow()
        expired_ips = [
            ip for ip, info in self.blocked_ips.items()
            if info['blocked_until'] and current_time > info['blocked_until']
        ]
        
        for ip in expired_ips:
            del self.blocked_ips[ip]
            logger.info(f"Cleaned up expired block for IP {ip}")
        
        return self.blocked_ips.copy()
    
    def get_block_info(self, ip: str) -> Optional[Dict]:
        """Get detailed block information for an IP"""
        return self.blocked_ips.get(ip)
    
    def update_block_reason(self, ip: str, new_reason: str) -> bool:
        """Update the reason for blocking an IP"""
        if ip in self.blocked_ips:
            self.blocked_ips[ip]['reason'] = new_reason
            logger.info(f"Updated block reason for IP {ip}: {new_reason}")
            return True
        return False
    
    def extend_block(self, ip: str, additional_time: timedelta) -> bool:
        """Extend the block duration for an IP"""
        if ip in self.blocked_ips:
            current_block = self.blocked_ips[ip]
            if current_block['blocked_until']:
                current_block['blocked_until'] += additional_time
                logger.info(f"Extended block for IP {ip} by {additional_time}")
                return True
        return False
    
    def get_block_statistics(self) -> Dict[str, Any]:
        """Get statistics about blocked IPs"""
        current_blocks = self.get_blocked_ips()
        
        level_counts = {}
        for info in current_blocks.values():
            level = info['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            'total_blocked': len(current_blocks),
            'by_level': level_counts,
            'permanent_blocks': level_counts.get('permanent', 0),
            'temporary_blocks': level_counts.get('temporary', 0),
            'extended_blocks': level_counts.get('extended', 0)
        }

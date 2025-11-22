#!/usr/bin/env python3
"""
Project Reorganization Script | 프로젝트 재구성 스크립트
========================================================

This script reorganizes the ShortFactory project structure to improve
maintainability by moving files to appropriate subdirectories.

이 스크립트는 파일을 적절한 하위 디렉토리로 이동하여 ShortFactory
프로젝트 구조를 재구성하고 유지보수성을 향상시킵니다.

Usage | 사용법:
    python scripts/reorganize_project.py [--dry-run]
    
Options | 옵션:
    --dry-run    Show what would be moved without actually moving files
                 실제로 파일을 이동하지 않고 이동될 파일만 표시
"""

import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


# Define file moves: source -> destination
# 파일 이동 정의: 소스 -> 대상
MOVES: Dict[str, str] = {
    # Documentation → docs/guides/
    "DEVELOPER_GUIDE.md": "docs/guides/DEVELOPER_GUIDE.md",
    "CONTRIBUTING.md": "docs/guides/CONTRIBUTING.md",
    "CLAUDE.md": "docs/guides/CLAUDE.md",
    
    # Knowledge transfer → docs/knowledge/
    "project_knowledge_transfer.md": "docs/knowledge/project_knowledge_transfer.md",
    
    # Scripts → scripts/
    "test_logging.py": "scripts/test_logging.py",
    "convert_logging.py": "scripts/convert_logging.py",
    "demo.py": "scripts/demo.py",
    
    # Notebooks → notebooks/
    "AIVCP.ipynb": "notebooks/AIVCP.ipynb",
    
    # Docker → docker/
    "Dockerfile": "docker/Dockerfile",
    "docker-compose.yml": "docker/docker-compose.yml",
    ".dockerignore": "docker/.dockerignore",
    
    # Config → config/
    ".env.example": "config/.env.example",
}


class ProjectReorganizer:
    """Handles project reorganization with dry-run support."""
    
    def __init__(self, root_dir: Path, dry_run: bool = False):
        """
        Initialize reorganizer.
        
        Args:
            root_dir: Project root directory
            dry_run: If True, only show what would be done
        """
        self.root = root_dir
        self.dry_run = dry_run
        self.moved: List[Tuple[str, str]] = []
        self.skipped: List[Tuple[str, str]] = []
        self.errors: List[Tuple[str, str]] = []
    
    def create_directories(self) -> None:
        """Create necessary subdirectories."""
        directories = [
            "docs/guides",
            "docs/knowledge",
            "docs/architecture",
            "docker",
            "config",
        ]
        
        print("\n📁 Creating directories | 디렉토리 생성 중...")
        print("=" * 60)
        
        for dir_path in directories:
            full_path = self.root / dir_path
            
            if full_path.exists():
                print(f"  ⏭️  Skip (exists): {dir_path}")
            elif self.dry_run:
                print(f"  🔍 Would create: {dir_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ Created: {dir_path}")
    
    def move_files(self) -> None:
        """Move files according to MOVES mapping."""
        print("\n📦 Moving files | 파일 이동 중...")
        print("=" * 60)
        
        for src, dst in MOVES.items():
            src_path = self.root / src
            dst_path = self.root / dst
            
            # Check if source exists
            if not src_path.exists():
                print(f"  ⚠️  Skip (not found): {src}")
                self.skipped.append((src, "Source file not found"))
                continue
            
            # Check if destination already exists
            if dst_path.exists():
                print(f"  ⚠️  Skip (dest exists): {src} → {dst}")
                self.skipped.append((src, "Destination already exists"))
                continue
            
            # Perform move
            if self.dry_run:
                print(f"  🔍 Would move: {src} → {dst}")
                self.moved.append((src, dst))
            else:
                try:
                    # Ensure destination directory exists
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Move file
                    shutil.move(str(src_path), str(dst_path))
                    print(f"  ✅ Moved: {src} → {dst}")
                    self.moved.append((src, dst))
                    
                except Exception as e:
                    print(f"  ❌ Error moving {src}: {e}")
                    self.errors.append((src, str(e)))
    
    def print_summary(self) -> None:
        """Print reorganization summary."""
        print("\n" + "=" * 60)
        print("📊 Summary | 요약")
        print("=" * 60)
        
        print(f"\n✅ Files moved: {len(self.moved)}")
        if self.moved:
            for src, dst in self.moved:
                print(f"   • {src} → {dst}")
        
        if self.skipped:
            print(f"\n⏭️  Files skipped: {len(self.skipped)}")
            for src, reason in self.skipped:
                print(f"   • {src} ({reason})")
        
        if self.errors:
            print(f"\n❌ Errors: {len(self.errors)}")
            for src, error in self.errors:
                print(f"   • {src}: {error}")
        
        if self.dry_run:
            print("\n🔍 DRY RUN MODE - No files were actually moved")
            print("   Run without --dry-run to perform actual reorganization")
        else:
            print("\n✨ Reorganization complete!")
    
    def run(self) -> bool:
        """
        Execute reorganization.
        
        Returns:
            bool: True if successful, False if errors occurred
        """
        print("🚀 ShortFactory Project Reorganization")
        print("=" * 60)
        print(f"Root directory: {self.root}")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        
        self.create_directories()
        self.move_files()
        self.print_summary()
        
        return len(self.errors) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Reorganize ShortFactory project structure"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it"
    )
    
    args = parser.parse_args()
    
    # Get project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    
    # Run reorganization
    reorganizer = ProjectReorganizer(root_dir, dry_run=args.dry_run)
    success = reorganizer.run()
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()

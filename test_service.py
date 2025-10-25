#!/usr/bin/env python3
"""
Test script for the Local Image Service
Run this script to verify that the service is working correctly
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8003"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ Could not connect to the service. Is it running?")
        return False

def test_create_project():
    """Test creating a project"""
    print("\n🔍 Testing project creation...")
    try:
        data = {
            "name": "Test Project",
            "description": "A test project for the multi-provider image service"
        }
        response = requests.post(f"{BASE_URL}/projects/", json=data)
        if response.status_code == 200:
            project = response.json()
            print("✅ Project created successfully")
            print(f"   Project ID: {project['id']}")
            print(f"   Project Name: {project['name']}")
            return project['id']
        else:
            print(f"❌ Project creation failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Project creation failed with error: {e}")
        return None

def test_providers():
    """Test provider status and availability"""
    print("\n🔍 Testing provider status...")
    try:
        response = requests.get(f"{BASE_URL}/unified/providers")
        if response.status_code == 200:
            data = response.json()
            providers = data.get("providers", {})
            total_available = data.get("total_available", 0)
            
            print(f"✅ Found {total_available} available providers")
            for provider_name, provider_info in providers.items():
                status = "✅ Available" if provider_info.get("available") else "❌ Unavailable"
                print(f"   {provider_name}: {status}")
                if not provider_info.get("available") and "error" in provider_info:
                    print(f"      Error: {provider_info['error']}")
            
            return total_available > 0
        else:
            print(f"❌ Provider status check failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Provider status check failed with error: {e}")
        return False

def test_quick_generation(project_id):
    """Test quick image generation"""
    if not project_id:
        print("\n⏭️ Skipping generation test - no project ID")
        return False
        
    print("\n🔍 Testing quick image generation...")
    try:
        data = {
            "prompt": "A beautiful sunset over mountains, digital art",
            "project_id": project_id,
            "num_images": 1
        }
        
        print("   Making generation request...")
        response = requests.post(f"{BASE_URL}/unified/generate/quick", json=data, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status")
            provider = result.get("provider")
            num_images = result.get("total_images", 0)
            
            print(f"✅ Generation completed with {provider}")
            print(f"   Status: {status}")
            print(f"   Images generated: {num_images}")
            
            if result.get("error_message"):
                print(f"   Warning: {result['error_message']}")
            
            return status == "completed" and num_images > 0
        else:
            print(f"❌ Generation failed with status {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Generation test failed with error: {e}")
        return False

def test_list_projects():
    """Test listing projects"""
    print("\n🔍 Testing project listing...")
    try:
        response = requests.get(f"{BASE_URL}/projects/")
        if response.status_code == 200:
            projects = response.json()
            print(f"✅ Found {len(projects)} projects")
            for project in projects[:3]:  # Show first 3
                print(f"   - {project['name']} ({project['id']})")
            return True
        else:
            print(f"❌ Project listing failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Project listing failed with error: {e}")
        return False

def test_storage_stats():
    """Test storage statistics"""
    print("\n🔍 Testing storage statistics...")
    try:
        response = requests.get(f"{BASE_URL}/storage/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Storage stats retrieved")
            print(f"   Total projects: {stats.get('total_projects', 0)}")
            print(f"   Total images: {stats.get('total_images', 0)}")
            print(f"   Storage path: {stats.get('base_path', 'N/A')}")
            return True
        else:
            print(f"❌ Storage stats failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Storage stats failed with error: {e}")
        return False

def test_api_docs():
    """Test that API documentation is accessible"""
    print("\n🔍 Testing API documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ API documentation is accessible")
            print(f"   Visit: {BASE_URL}/docs")
            return True
        else:
            print(f"❌ API docs failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs failed with error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Multi-Provider Image Generation Service Test Suite")
    print("=" * 60)
    
    # Test service connectivity
    if not test_health():
        print("\n❌ Service is not running. Please start it with: python main.py")
        return False
    
    # Test provider system
    providers_available = test_providers()
    
    # Test core functionality
    test_list_projects()
    project_id = test_create_project()
    test_storage_stats()
    test_api_docs()
    
    # Test image generation if providers are available
    if providers_available and project_id:
        test_quick_generation(project_id)
    
    print("\n" + "=" * 60)
    print("🎉 Test suite completed!")
    print(f"📚 API Documentation: {BASE_URL}/docs")
    print(f"🔄 Interactive API: {BASE_URL}/redoc")
    print(f"🎯 Unified Generation: {BASE_URL}/unified/generate/quick")
    
    if project_id:
        print(f"\n💡 Project created: {project_id}")
        print("   Try the unified generation endpoints:")
        print(f"   • Quick generation: POST {BASE_URL}/unified/generate/quick")
        print(f"   • Full generation: POST {BASE_URL}/unified/generate")
        print(f"   • Provider status: GET {BASE_URL}/unified/providers")
    
    return True

if __name__ == "__main__":
    main()
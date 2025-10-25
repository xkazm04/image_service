# Multi-Provider Image Generation Service

A sophisticated, unified image generation service that seamlessly integrates multiple AI providers with intelligent prompt optimization, automatic fallback mechanisms, and comprehensive local storage management.

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Application                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │   Unified API   │  │ Prompt Validation │  │ Storage Manager │ │
│  │    Routes       │  │   & Optimization  │  │                 │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Unified Generation Service                     │ │
│  │  • Provider Selection & Load Balancing                     │ │
│  │  • Automatic Fallback & Retry Logic                        │ │
│  │  • Request Normalization & Response Mapping                │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐ │
│  │ Leonardo AI  │ │ Runware AI   │ │ Gemini Image │ │ ComfyUI │ │
│  │   Provider   │ │   Provider   │ │   Provider   │ │Provider │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐ │
│  │ Ollama Service  │  │ Supabase Database│  │ Local Storage   │ │
│  │ (gpt-oss:20b)   │  │   PostgreSQL     │  │   File System   │ │
│  └─────────────────┘  └──────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Core Features

### **🤖 Multi-Provider AI Integration**

**Supported Providers:**
- **Leonardo AI** - Premium quality with diverse models and styles
- **Runware AI** - High-performance generation with excellent speed
- **Gemini Image Generation** - Google's Gemini 2.5 Flash with SynthID watermarking
- **ComfyUI (Local)** - Local server integration with Flux Dev model

**Key Capabilities:**
- **Universal Interface**: Single API that works transparently across all providers
- **Intelligent Selection**: Automatic provider selection based on request parameters
- **Automatic Fallback**: Seamless retry with alternative providers on failure
- **Load Balancing**: Distributes requests to optimize performance and reliability

### **🧠 Advanced Prompt Management**

**Intelligent Validation & Optimization:**
- **Length Enforcement**: Returns HTTP 400 for prompts exceeding 10,000 characters
- **Automatic Optimization**: Uses Ollama LLM to compress prompts between 3,000-10,000 chars
- **Concept Preservation**: Maintains artistic intent while reducing redundancy
- **Real-time Analysis**: Provides complexity scores, readability metrics, and keyword extraction

**Optimization Engine:**
- **Model**: `gpt-oss:20b` via Ollama (`localhost:11434`)
- **Strategy**: Preserves quality terms, style keywords, and core concepts
- **Target**: Optimizes to under 3,000 characters for maximum provider compatibility
- **Fallback**: Graceful degradation when Ollama is unavailable

### **💾 Comprehensive Data Management**

**Supabase Integration:**
- **PostgreSQL Database**: Extends existing project schema
- **Generation Tracking**: Complete job lifecycle monitoring
- **Provider Analytics**: Performance metrics and usage statistics
- **Relationship Mapping**: Links images to projects and user workflows

**Local Storage System:**
```
storage/
└── images/
    └── {project-id}/
        ├── leonardo_ai/
        ├── runware_ai/
        ├── gemini/
        └── comfyui/
```

**Storage Features:**
- **Organized Structure**: Provider-specific directories with project isolation
- **Automatic Download**: Fetches and stores images from cloud providers
- **File Serving**: Static file serving with proper MIME types
- **Cleanup Utilities**: Storage management and optimization tools

### **🔄 Unified Generation Workflow**

**Request Processing Pipeline:**
1. **Input Validation**: Validates request parameters and formats
2. **Prompt Optimization**: Analyzes and optimizes prompts if needed
3. **Provider Selection**: Chooses optimal provider based on capabilities
4. **Generation Execution**: Sends normalized request to selected provider
5. **Response Processing**: Downloads images and normalizes response format
6. **Storage Management**: Organizes files and updates database records
7. **Fallback Handling**: Retries with alternative providers if needed

**Response Standardization:**
```json
{
  "generation_id": "uuid",
  "provider": "leonardo_ai",
  "status": "completed",
  "prompt": "optimized prompt text",
  "images": [
    {
      "id": "image_id",
      "url": "original_provider_url",
      "local_url": "/storage/images/project-id/provider/image.jpg",
      "width": 1024,
      "height": 1024,
      "format": "jpeg"
    }
  ],
  "metadata": {
    "prompt_validation": {
      "original_length": 4500,
      "optimized_length": 2800,
      "optimization_time": 3.2
    },
    "generation_time": 8.5,
    "provider_model": "Leonardo Kino XL"
  }
}
```

## 🛠️ Technical Architecture

### **Core Components**

**`services/unified_generation.py`**
- Central orchestration service
- Provider selection and fallback logic
- Request normalization and response mapping
- Generation job tracking and status management

**`services/prompt_validation.py`**
- Prompt length validation and error handling
- Ollama integration for intelligent optimization
- Concept preservation algorithms
- Performance metrics and analytics

**`services/providers/`**
- Individual provider implementations
- Universal interface compliance
- Provider-specific parameter mapping
- Error handling and status reporting

**`services/ollama/`**
- Reusable Ollama client with async support
- Connection management and health monitoring
- Retry logic and timeout handling
- Model availability detection

### **API Architecture**

**RESTful Design:**
- **FastAPI Framework**: Automatic documentation and validation
- **Async Processing**: Non-blocking concurrent operations
- **CORS Support**: Cross-origin resource sharing for web integration
- **Error Handling**: Comprehensive HTTP status codes and error messages

**Key Endpoints:**
```
POST   /unified/generate          # Main generation endpoint
POST   /unified/generate/quick    # Simplified generation
POST   /unified/generate/batch    # Batch processing
POST   /unified/validate-prompt   # Prompt optimization
GET    /unified/providers         # Provider status
GET    /unified/jobs             # Generation history
```

### **Database Schema**

**Extended Supabase Tables:**
- **`generation_jobs`**: Complete generation tracking
- **`provider_configs`**: Dynamic provider configuration
- **`images`**: Enhanced metadata with provider information
- **`projects`**: Existing project integration

**Performance Optimizations:**
- Indexed queries for fast retrieval
- Connection pooling for concurrent access
- Transaction management for data consistency
- Row-level security (RLS) policies

## 🚀 Getting Started

### **Prerequisites**
```bash
# Python 3.8+ with virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### **Configuration**
```bash
# Copy environment template
cp .env.example .env

# Configure required variables
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key
LEONARDO_API_KEY=your_leonardo_key
RUNWARE_API_KEY=your_runware_key
GEMINI_API_KEY=your_gemini_key
```

### **Ollama Setup (For Prompt Optimization)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server
ollama serve

# Pull the optimization model
ollama pull gpt-oss:20b
```

### **Launch Service**
```bash
python main.py
```
Service available at: `http://localhost:8003`
API Documentation: `http://localhost:8003/docs`

## 📊 Monitoring & Analytics

### **Health Monitoring**
- **Service Health**: `GET /health`
- **Provider Status**: `GET /unified/providers`
- **Ollama Availability**: `GET /unified/prompt-validator/health`

### **Performance Metrics**
- Generation success rates by provider
- Average response times and optimization performance
- Storage usage and cleanup statistics
- Prompt optimization effectiveness metrics

### **Logging & Debugging**
- Structured logging with configurable levels
- Request/response tracing for debugging
- Error aggregation and alerting
- Performance profiling and bottleneck identification

## 🔧 Development & Testing

### **Testing Suite**
```bash
# Run comprehensive tests
python test_prompt_validation.py
python test_service.py

# Test individual components
python -m pytest tests/
```

### **Development Tools**
- **Hot Reload**: `uvicorn main:app --reload`
- **Debug Mode**: Enhanced error messages and stack traces
- **API Testing**: Automatic OpenAPI/Swagger documentation
- **Database Migrations**: Supabase schema management

### **Code Organization**
```
image/
├── services/           # Core business logic
│   ├── unified_generation.py
│   ├── prompt_validation.py
│   ├── providers/      # Provider implementations
│   └── ollama/         # Ollama client
├── routes/             # API endpoints
├── models/             # Database models
├── utils/              # Utility functions
├── prompts/            # Optimization templates
└── storage/            # Local file storage
```

## 🔒 Security & Best Practices

### **Security Measures**
- **Local Binding**: Service runs on `127.0.0.1` for security
- **API Key Management**: Secure environment variable handling
- **Input Validation**: Comprehensive request sanitization
- **Rate Limiting**: Provider-specific request throttling

### **Best Practices**
- **Error Handling**: Graceful degradation and meaningful error messages
- **Resource Management**: Proper cleanup and connection pooling
- **Async Operations**: Non-blocking I/O for optimal performance
- **Logging**: Comprehensive audit trails and debugging information

## 🎨 Use Cases

### **Content Creation**
- **Marketing Materials**: Brand-consistent image generation
- **Social Media**: Batch generation for campaigns
- **Product Visualization**: Multiple style variations
- **Creative Exploration**: Rapid prototyping and iteration

### **Development Integration**
- **Web Applications**: Direct API integration
- **Mobile Apps**: RESTful API consumption
- **Batch Processing**: Automated content generation
- **Workflow Automation**: Integration with existing pipelines

## 🚦 Roadmap

### **Planned Enhancements**
- **Advanced Provider Logic**: ML-based provider selection
- **Caching Layer**: Redis integration for improved performance
- **Image Processing**: Built-in filters and transformations
- **Analytics Dashboard**: Real-time usage monitoring
- **Webhook Support**: Event-driven integrations
- **Multi-tenant Support**: Organization-level isolation

### **Performance Optimizations**
- **Request Batching**: Improved throughput for bulk operations
- **CDN Integration**: Global image delivery
- **Background Processing**: Queue-based generation
- **Smart Caching**: Intelligent response caching

---

## 📄 License

This project is part of the KIRO workspace ecosystem. See the main repository for licensing information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

**Built with ❤️ for the KIRO ecosystem**
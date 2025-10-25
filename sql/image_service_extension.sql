-- ============================================
-- Image Service Extension for Supabase
-- Extends the existing Story App schema with image generation tables
-- ============================================

-- NOTE: This assumes the Story App schema (01_schema.sql) is already applied
-- The 'projects' table already exists and will be referenced by foreign keys

-- ============================================
-- IMAGES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS images (
    internal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    id VARCHAR(255) NOT NULL UNIQUE, -- Provider image ID or custom ID
    url VARCHAR(500), -- Original provider URL (optional)
    local_path VARCHAR(500), -- Local file path
    local_url VARCHAR(500), -- Local URL for serving
    
    -- Relationships (references existing projects table)
    scene_id UUID, -- References scenes.id (optional)
    project_id UUID NOT NULL, -- References existing projects.id
    
    -- Prompt information  
    prompt_artstyle TEXT,
    prompt_scenery TEXT,
    prompt_actor TEXT,
    full_prompt TEXT, -- Complete prompt used for generation
    
    -- Provider information
    provider VARCHAR(50) DEFAULT 'leonardo', -- leonardo, runware, gemini, comfyui
    provider_model_id VARCHAR(255), -- Provider-specific model ID
    
    -- Metadata
    type VARCHAR(50) DEFAULT 'generated', -- generated, uploaded, variation
    tags TEXT, -- Comma-separated tags
    generation_id VARCHAR(255), -- Provider generation ID
    
    -- Status and timestamps
    status VARCHAR(50) NOT NULL DEFAULT 'active', -- active, deleted, archived
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- File information
    file_size BIGINT, -- File size in bytes
    file_format VARCHAR(10), -- jpg, png, webp, etc.
    dimensions VARCHAR(20), -- "512x512"
    
    -- Generation parameters (stored for reference)
    width INTEGER,
    height INTEGER,
    seed BIGINT,
    steps INTEGER,
    guidance_scale DECIMAL(4,2)
);

-- ============================================
-- IMAGE VARIANTS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS image_variants (
    id VARCHAR(255) PRIMARY KEY,
    image_id UUID NOT NULL REFERENCES images(internal_id) ON DELETE CASCADE,
    is_primary BOOLEAN NOT NULL DEFAULT true,
    variant_type VARCHAR(50) NOT NULL DEFAULT 'main', -- main, upscale, variation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- GENERATION JOBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS generation_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    generation_id VARCHAR(255) NOT NULL, -- Provider generation ID (unique per provider)
    provider VARCHAR(50) NOT NULL, -- leonardo, runware, gemini, comfyui
    project_id UUID NOT NULL, -- References existing projects.id
    
    -- Generation parameters
    prompt TEXT NOT NULL,
    negative_prompt TEXT,
    width INTEGER,
    height INTEGER,
    num_images INTEGER DEFAULT 1,
    model_id VARCHAR(255),
    preset_style VARCHAR(50),
    seed BIGINT,
    guidance_scale DECIMAL(4,2),
    steps INTEGER,
    
    -- Provider-specific parameters (JSON)
    provider_params JSONB,
    
    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Results
    result_images JSONB, -- Array of generated image data
    cost DECIMAL(10,6), -- Generation cost
    
    UNIQUE(provider, generation_id) -- Unique per provider
);

-- ============================================
-- PROVIDER CONFIGURATIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS provider_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider VARCHAR(50) NOT NULL UNIQUE, -- leonardo, runware, gemini, comfyui
    name VARCHAR(100) NOT NULL,
    description TEXT,
    base_url VARCHAR(500),
    api_key_env VARCHAR(100), -- Environment variable name for API key
    is_enabled BOOLEAN DEFAULT true,
    default_model VARCHAR(255),
    supported_formats TEXT[], -- Array of supported image formats
    max_width INTEGER,
    max_height INTEGER,
    max_images INTEGER,
    
    -- Rate limiting
    rate_limit_per_minute INTEGER,
    rate_limit_per_hour INTEGER,
    
    -- Configuration schema (JSON)
    config_schema JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX idx_images_project_id ON images(project_id);
CREATE INDEX idx_images_provider ON images(provider);
CREATE INDEX idx_images_status ON images(status);
CREATE INDEX idx_images_generation_id ON images(generation_id);
CREATE INDEX idx_images_created_at ON images(created_at);
CREATE INDEX idx_images_scene_id ON images(scene_id);

CREATE INDEX idx_image_variants_image_id ON image_variants(image_id);
CREATE INDEX idx_image_variants_type ON image_variants(variant_type);

CREATE INDEX idx_generation_jobs_provider ON generation_jobs(provider);
CREATE INDEX idx_generation_jobs_status ON generation_jobs(status);
CREATE INDEX idx_generation_jobs_project_id ON generation_jobs(project_id);
CREATE INDEX idx_generation_jobs_created_at ON generation_jobs(created_at);

CREATE INDEX idx_provider_configs_provider ON provider_configs(provider);
CREATE INDEX idx_provider_configs_enabled ON provider_configs(is_enabled);

-- ============================================
-- UPDATE TRIGGERS
-- ============================================

-- Apply update trigger to new tables
CREATE TRIGGER update_images_updated_at BEFORE UPDATE ON images
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_generation_jobs_updated_at BEFORE UPDATE ON generation_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_provider_configs_updated_at BEFORE UPDATE ON provider_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on image tables
ALTER TABLE images ENABLE ROW LEVEL SECURITY;
ALTER TABLE image_variants ENABLE ROW LEVEL SECURITY;
ALTER TABLE generation_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE provider_configs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- RLS POLICIES
-- ============================================

-- Images: Users can access images from their projects
CREATE POLICY "Users can view images from own projects" ON images
    FOR SELECT USING (project_id IN (
        SELECT id FROM projects WHERE user_id IN (
            SELECT id FROM users WHERE clerk_id = auth.uid()::text
        )
    ));

CREATE POLICY "Users can manage images in own projects" ON images
    FOR ALL USING (project_id IN (
        SELECT id FROM projects WHERE user_id IN (
            SELECT id FROM users WHERE clerk_id = auth.uid()::text
        )
    ));

-- Image variants: Access through images
CREATE POLICY "Users can view image variants" ON image_variants
    FOR SELECT USING (image_id IN (
        SELECT internal_id FROM images WHERE project_id IN (
            SELECT id FROM projects WHERE user_id IN (
                SELECT id FROM users WHERE clerk_id = auth.uid()::text
            )
        )
    ));

CREATE POLICY "Users can manage image variants" ON image_variants
    FOR ALL USING (image_id IN (
        SELECT internal_id FROM images WHERE project_id IN (
            SELECT id FROM projects WHERE user_id IN (
                SELECT id FROM users WHERE clerk_id = auth.uid()::text
            )
        )
    ));

-- Generation jobs: Users can access their own jobs
CREATE POLICY "Users can view own generation jobs" ON generation_jobs
    FOR SELECT USING (project_id IN (
        SELECT id FROM projects WHERE user_id IN (
            SELECT id FROM users WHERE clerk_id = auth.uid()::text
        )
    ));

CREATE POLICY "Users can manage own generation jobs" ON generation_jobs
    FOR ALL USING (project_id IN (
        SELECT id FROM projects WHERE user_id IN (
            SELECT id FROM users WHERE clerk_id = auth.uid()::text
        )
    ));

-- Provider configs: Read-only for all authenticated users
CREATE POLICY "Authenticated users can view provider configs" ON provider_configs
    FOR SELECT USING (auth.uid() IS NOT NULL);

-- ============================================
-- SEED DATA
-- ============================================

-- Insert provider configurations
INSERT INTO provider_configs (provider, name, description, base_url, api_key_env, default_model, supported_formats, max_width, max_height, max_images, config_schema) VALUES
('leonardo', 'Leonardo AI', 'High-quality AI image generation with various models and styles', 'https://cloud.leonardo.ai/api/rest/v1', 'LEONARDO_API_KEY', 'de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3', ARRAY['jpg', 'png', 'webp'], 1024, 1024, 8, 
 '{"models": [{"id": "de7d3faf-762f-48e0-b3b7-9d0ac3a3fcf3", "name": "Phoenix 1.0"}], "presetStyles": ["DYNAMIC", "CREATIVE", "PHOTOGRAPHY", "SKETCH_BW"]}'::jsonb),

('runware', 'Runware AI', 'Fast and scalable AI image generation with multiple models', 'https://api.runware.ai', 'RUNWARE_API_KEY', 'runware:100@1', ARRAY['jpg', 'png', 'webp'], 2048, 2048, 20,
 '{"outputTypes": ["URL", "base64Data", "dataURI"], "models": ["runware:100@1", "runware:101@1"]}'::jsonb),

('gemini', 'Gemini Image Generation', 'Google Gemini 2.5 Flash image generation', 'https://generativelanguage.googleapis.com', 'GEMINI_API_KEY', 'gemini-2.5-flash-image', ARRAY['png'], 1024, 1024, 1,
 '{"aspectRatios": ["1:1", "16:9", "9:16", "4:3", "3:4"]}'::jsonb),

('comfyui', 'ComfyUI (Local)', 'Local ComfyUI server with Flux Dev model', 'http://localhost:8188', null, 'flux-dev', ARRAY['png', 'jpg'], 1024, 1024, 4,
 '{"workflows": ["text-to-image"], "models": ["flux-dev"]}'::jsonb);

-- ============================================
-- COMPLETED
-- ============================================
-- Image service extension complete!
-- This extends the existing Story App schema with image generation capabilities
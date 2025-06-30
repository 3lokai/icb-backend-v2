-- Supabase Functions for Coffee Related Data Management
-- These functions handle the upsert operations for brew methods, flavor profiles, and external links

-- Function to upsert a brew method and link it to a coffee
CREATE OR REPLACE FUNCTION upsert_brew_method_and_link(coffee_id UUID, method_name TEXT)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    brew_method_id UUID;
BEGIN
    -- First, try to find existing brew method by name
    SELECT id INTO brew_method_id 
    FROM brew_methods 
    WHERE LOWER(name) = LOWER(method_name);
    
    -- If not found, create new brew method
    IF brew_method_id IS NULL THEN
        INSERT INTO brew_methods (name) 
        VALUES (method_name)
        RETURNING id INTO brew_method_id;
    END IF;
    
    -- Link brew method to coffee (ignore if already linked)
    INSERT INTO coffee_brew_methods (coffee_id, brew_method_id)
    VALUES (coffee_id, brew_method_id)
    ON CONFLICT (coffee_id, brew_method_id) DO NOTHING;
    
    RETURN brew_method_id;
END;
$$;

-- Function to upsert a flavor profile and link it to a coffee
CREATE OR REPLACE FUNCTION upsert_flavor_and_link(coffee_id UUID, flavor_name TEXT)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    flavor_id UUID;
BEGIN
    -- First, try to find existing flavor by name
    SELECT id INTO flavor_id 
    FROM flavor_profiles 
    WHERE LOWER(name) = LOWER(flavor_name);
    
    -- If not found, create new flavor
    IF flavor_id IS NULL THEN
        INSERT INTO flavor_profiles (name) 
        VALUES (flavor_name)
        RETURNING id INTO flavor_id;
    END IF;
    
    -- Link flavor to coffee (ignore if already linked)
    INSERT INTO coffee_flavor_profiles (coffee_id, flavor_id)
    VALUES (coffee_id, flavor_id)
    ON CONFLICT (coffee_id, flavor_id) DO NOTHING;
    
    RETURN flavor_id;
END;
$$;

-- Function to upsert an external link for a coffee
CREATE OR REPLACE FUNCTION upsert_external_link(coffee_id UUID, provider_name TEXT, link_url TEXT)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    link_id UUID;
BEGIN
    -- Check if link already exists for this coffee and provider
    SELECT id INTO link_id 
    FROM external_links 
    WHERE coffee_id = upsert_external_link.coffee_id 
    AND provider = provider_name;
    
    -- If exists, update the URL
    IF link_id IS NOT NULL THEN
        UPDATE external_links 
        SET url = link_url, updated_at = NOW()
        WHERE id = link_id;
    ELSE
        -- Create new external link
        INSERT INTO external_links (coffee_id, provider, url)
        VALUES (coffee_id, provider_name, link_url)
        RETURNING id INTO link_id;
    END IF;
    
    RETURN link_id;
END;
$$;

-- Function to upsert a region by name
CREATE OR REPLACE FUNCTION upsert_region(region_name TEXT)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    region_id UUID;
BEGIN
    -- First, try to find existing region by name
    SELECT id INTO region_id 
    FROM regions 
    WHERE LOWER(name) = LOWER(region_name);
    
    -- If not found, create new region
    IF region_id IS NULL THEN
        INSERT INTO regions (name) 
        VALUES (region_name)
        RETURNING id INTO region_id;
    END IF;
    
    RETURN region_id;
END;
$$;

-- Grant execute permissions to authenticated users
GRANT EXECUTE ON FUNCTION upsert_brew_method_and_link(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION upsert_flavor_and_link(UUID, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION upsert_external_link(UUID, TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION upsert_region(TEXT) TO authenticated; 
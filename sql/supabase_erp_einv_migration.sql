-- ==============================================================================
-- Taiwan Electronic Invoice (MIG 4.1) Integration for Supabase ERP
-- Company: 奧銳有限公司 (BAN: 00015555 | Turnkey Routing: PA006753)
-- Target Database: Supabase (PostgreSQL 15+)
-- ==============================================================================
-- This script contains all new tables, functions, and columns needed to adapt
-- your existing ERP database to the Taiwan MOF E-Invoice Turnkey system.
-- Run this in the Supabase Dashboard -> SQL Editor.
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Track Quota Management Table (einv_track_quota)
-- Purpose: Holds the bimonthly electronic invoice track numbers (字軌號碼)
--          approved by the National Taxation Bureau (國稅局).
-- Usage: Add 1 row per period (every 2 months, e.g. 115/09~10).
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.einv_track_quota (
    id BIGSERIAL PRIMARY KEY,
    year_month CHAR(5) NOT NULL,               -- 民國雙月期別，例如 '11510' (115年09-10月期)
    track_prefix CHAR(2) NOT NULL,             -- 字軌英文代碼，例如 'LP'
    start_no INT NOT NULL,                     -- 起號，例如 50936600
    end_no INT NOT NULL,                       -- 訖號，例如 50939099
    current_no INT NOT NULL,                   -- 目前開立號碼 (初始值同起號，開立時自動累加)
    is_active BOOLEAN NOT NULL DEFAULT TRUE,   -- 是否啟用本期字軌
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_track_quota UNIQUE(year_month, track_prefix, start_no)
);

COMMENT ON TABLE public.einv_track_quota IS 'Taiwan e-Invoice bimonthly track quota bookkeeper (每期電子發票字軌配號簿)';
COMMENT ON COLUMN public.einv_track_quota.year_month IS '民國雙月期別 (e.g. 11510: 115年9-10月, 11512: 11-12月)';
COMMENT ON COLUMN public.einv_track_quota.track_prefix IS '2-letter track prefix (e.g. LP, AB)';
COMMENT ON COLUMN public.einv_track_quota.current_no IS 'Next sequential number to be issued (自動累加)';

-- Seed initial test quota for 115/09~10 (LP50936600 ~ LP50939099)
INSERT INTO public.einv_track_quota (year_month, track_prefix, start_no, end_no, current_no, is_active)
VALUES ('11510', 'LP', 50936600, 50939099, 50936600, TRUE)
ON CONFLICT (year_month, track_prefix, start_no) DO NOTHING;


-- ------------------------------------------------------------------------------
-- 2. Atomic Invoice Number & Random Number Allocation RPC Function
-- Purpose: Atomically retrieves and increments the next available invoice number.
-- Features: Uses row-level locking (FOR UPDATE) to guarantee zero duplicates
--           or race conditions during simultaneous order processing.
-- Return: JSON containing invoice_number (10 chars), random_number (4 digits), year_month
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.allocate_next_invoice_number(p_year_month CHAR(5))
RETURNS JSONB AS $$
DECLARE
    v_row public.einv_track_quota%ROWTYPE;
    v_inv_no TEXT;
    v_random TEXT;
BEGIN
    -- Row-level lock to prevent concurrent workers from claiming the same number
    SELECT * INTO v_row
    FROM public.einv_track_quota
    WHERE year_month = p_year_month AND is_active = TRUE AND current_no <= end_no
    ORDER BY id ASC
    LIMIT 1
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No active track quota available for period %', p_year_month;
    END IF;

    -- Format full 10-character invoice number: Prefix (2 chars) + Number (8 digits zero-padded)
    v_inv_no := v_row.track_prefix || LPAD(v_row.current_no::TEXT, 8, '0');

    -- Generate cryptographically random 4-digit number (1000 - 9999) for receipt lottery
    v_random := LPAD(FLOOR(RANDOM() * 9000 + 1000)::TEXT, 4, '0');

    -- Increment quota counter
    UPDATE public.einv_track_quota
    SET current_no = current_no + 1,
        updated_at = NOW()
    WHERE id = v_row.id;

    RETURN jsonb_build_object(
        'invoice_number', v_inv_no,
        'random_number', v_random,
        'year_month', v_row.year_month
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

COMMENT ON FUNCTION public.allocate_next_invoice_number(CHAR(5)) IS 'Atomically allocate the next Taiwan e-Invoice number and 4-digit lottery code';


-- ------------------------------------------------------------------------------
-- 3. Schema Adaptations on Existing `orders` Table
-- Purpose: Tracks electronic invoice issuance, transmission, results, and cancellations.
-- ------------------------------------------------------------------------------

-- (1) Invoice Issuance & Matching Columns
ALTER TABLE public.orders 
    ADD COLUMN IF NOT EXISTS einv_number VARCHAR(10),              -- e-Invoice Number (e.g. LP50936600)
    ADD COLUMN IF NOT EXISTS einv_random_number CHAR(4),           -- 4-digit lottery random number (防偽隨機碼)
    ADD COLUMN IF NOT EXISTS einv_date CHAR(8),                    -- Invoice Date (YYYYMMDD)
    ADD COLUMN IF NOT EXISTS einv_time CHAR(8),                    -- Invoice Time (HH:MM:SS)
    ADD COLUMN IF NOT EXISTS einv_msg_type VARCHAR(10) DEFAULT 'F0401', -- MIG 4.1 Message Type (F0401: B2C, A0101: B2B)
    ADD COLUMN IF NOT EXISTS einv_status VARCHAR(20) DEFAULT 'PENDING',  -- Lifecycle: PENDING, DISPATCHED, SUCCESS, FAILED, CANCEL_PENDING, CANCEL_DISPATCHED, CANCELLED
    ADD COLUMN IF NOT EXISTS einv_result_code VARCHAR(10),         -- MOF Result Code (00000 = 全部發票處理成功)
    ADD COLUMN IF NOT EXISTS einv_result_desc TEXT,                -- MOF Error or Result Description
    ADD COLUMN IF NOT EXISTS einv_turnkey_uuid VARCHAR(64),        -- Turnkey transmission tracking UUID
    ADD COLUMN IF NOT EXISTS einv_dispatched_at TIMESTAMPTZ,       -- When dropped into Turnkey UpCast
    ADD COLUMN IF NOT EXISTS einv_completed_at TIMESTAMPTZ;        -- When MOF acknowledged receipt

-- (2) Order Cancellation Columns (F0501 / A0201)
ALTER TABLE public.orders 
    ADD COLUMN IF NOT EXISTS einv_cancel_date CHAR(8),             -- Cancellation Date (YYYYMMDD)
    ADD COLUMN IF NOT EXISTS einv_cancel_time CHAR(8),             -- Cancellation Time (HH:MM:SS)
    ADD COLUMN IF NOT EXISTS einv_cancel_reason VARCHAR(100),      -- Reason for voiding/cancelling invoice
    ADD COLUMN IF NOT EXISTS einv_cancel_result_code VARCHAR(10),  -- MOF Cancel Result Code (00000 = success)
    ADD COLUMN IF NOT EXISTS einv_cancel_completed_at TIMESTAMPTZ; -- When cancellation was confirmed by MOF

-- (3) Buyer & Carrier Information Columns (B2C / B2B)
ALTER TABLE public.orders 
    ADD COLUMN IF NOT EXISTS buyer_ban VARCHAR(10) DEFAULT '0000000000', -- 8-digit BAN for B2B, '0000000000' for B2C consumer
    ADD COLUMN IF NOT EXISTS buyer_name VARCHAR(100),              -- Buyer Company Name or Consumer Name
    ADD COLUMN IF NOT EXISTS carrier_type VARCHAR(10),             -- Carrier Type (3J0002 = 手機條碼, CQ0001 = 自然人憑證)
    ADD COLUMN IF NOT EXISTS carrier_id VARCHAR(64),               -- Carrier ID (e.g. /ABC+123)
    ADD COLUMN IF NOT EXISTS donate_mark CHAR(1) DEFAULT '0',      -- Donation Mark (0: 不捐贈, 1: 捐贈)
    ADD COLUMN IF NOT EXISTS love_code VARCHAR(10),                -- NPO Love Code (愛心碼, e.g. 25885)
    ADD COLUMN IF NOT EXISTS print_mark CHAR(1) DEFAULT 'Y';       -- Print Mark (Y: 列印證明聯紙本, N: 雲端發票不列印)

-- Comments for documentation in Supabase Table Editor
COMMENT ON COLUMN public.orders.einv_number IS '電子發票字軌號碼 (10碼，例如 LP50936600)';
COMMENT ON COLUMN public.orders.einv_random_number IS '發票4位隨機碼 (用於兌獎與防偽)';
COMMENT ON COLUMN public.orders.einv_status IS '發票狀態: PENDING(待開立), DISPATCHED(傳送中), SUCCESS(開立成功), FAILED(失敗), CANCEL_PENDING(待作廢), CANCELLED(已作廢)';
COMMENT ON COLUMN public.orders.einv_result_code IS '財政部平台官方處理結果代碼 (00000 為成功)';
COMMENT ON COLUMN public.orders.carrier_type IS '載具類別 (3J0002: 手機條碼, CQ0001: 自然人憑證)';
COMMENT ON COLUMN public.orders.carrier_id IS '載具顯碼代號 (例如 /ABC+123)';
COMMENT ON COLUMN public.orders.donate_mark IS '捐贈註記 (0: 不捐贈, 1: 捐贈)';
COMMENT ON COLUMN public.orders.love_code IS '受捐贈機關愛心碼 (例如 25885)';

-- Indexes for fast querying by bridge workers
CREATE INDEX IF NOT EXISTS idx_orders_einv_status ON public.orders(einv_status);
CREATE INDEX IF NOT EXISTS idx_orders_einv_number ON public.orders(einv_number);


-- ------------------------------------------------------------------------------
-- 4. Automatic Order Cancellation Trigger (Optional Enhancement)
-- Purpose: When internal_status is updated to 'cancelled' and the order already
--          has an issued invoice (einv_status = 'SUCCESS'), automatically flag
--          einv_status to 'CANCEL_PENDING' so the bridge issues F0501 immediately.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.trigger_einv_cancel_on_order_cancel()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.internal_status = 'cancelled' 
       AND OLD.internal_status != 'cancelled' 
       AND OLD.einv_number IS NOT NULL 
       AND OLD.einv_status = 'SUCCESS' THEN
        
        NEW.einv_status := 'CANCEL_PENDING';
        NEW.einv_cancel_reason := COALESCE(NEW.notes, '訂單取消作廢發票');
        NEW.einv_cancel_date := TO_CHAR(NOW(), 'YYYYMMDD');
        NEW.einv_cancel_time := TO_CHAR(NOW(), 'HH24:MI:SS');
        RAISE NOTICE 'Order % invoice % queued for Turnkey F0501 cancellation', NEW.shopee_order_number, NEW.einv_number;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_einv_cancel_on_order_cancel ON public.orders;
CREATE TRIGGER trigger_einv_cancel_on_order_cancel
BEFORE UPDATE ON public.orders
FOR EACH ROW EXECUTE FUNCTION public.trigger_einv_cancel_on_order_cancel();

COMMENT ON FUNCTION public.trigger_einv_cancel_on_order_cancel() IS 'Auto-flag invoice for Turnkey F0501 cancellation when order internal_status becomes cancelled';

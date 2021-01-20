-- upgrade --
CREATE TABLE IF NOT EXISTS "eva_idp" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(32) NOT NULL,
    "type" VARCHAR(8) NOT NULL,
    "config" JSONB,
    "is_active" BOOL NOT NULL  DEFAULT False
);
COMMENT ON COLUMN "eva_idp"."type" IS 'IdP类型';
COMMENT ON COLUMN "eva_idp"."config" IS '该IdP的详细配置';
COMMENT ON COLUMN "eva_idp"."is_active" IS '该IdP是否启用？';
COMMENT ON TABLE "eva_idp" IS 'IdP';
CREATE TABLE IF NOT EXISTS "eva_identity" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "uuid" UUID NOT NULL UNIQUE,
    "is_active" BOOL NOT NULL  DEFAULT True
);
COMMENT ON TABLE "eva_identity" IS '用户 ';
CREATE TABLE IF NOT EXISTS "eva_credential" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "identifier" VARCHAR(64) NOT NULL,
    "identifier_type" VARCHAR(8) NOT NULL,
    "idp_id" BIGINT REFERENCES "eva_idp" ("id") ON DELETE CASCADE,
    "identity_id" BIGINT NOT NULL REFERENCES "eva_identity" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_eva_credent_identit_4dc08b" UNIQUE ("identity_id", "identifier")
);
COMMENT ON COLUMN "eva_credential"."identifier" IS '凭证唯一标识，如：邮件地址,手机号,微信openid等';
COMMENT ON COLUMN "eva_credential"."identifier_type" IS 'identifier 的类型，如用户名只能对应密码认证；邮件和手机号可以有其对应的验证码认证';
COMMENT ON TABLE "eva_credential" IS '凭证';
CREATE TABLE IF NOT EXISTS "eva_password" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "shadow" VARCHAR(512) NOT NULL,
    "expires_at" TIMESTAMPTZ,
    "credential_id" BIGINT NOT NULL REFERENCES "eva_credential" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "eva_password" IS '密码验证方式';
CREATE TABLE IF NOT EXISTS "eva_permission" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "code" VARCHAR(128) NOT NULL UNIQUE,
    "name" VARCHAR(128) NOT NULL,
    "description" TEXT
);
COMMENT ON TABLE "eva_permission" IS '提供“标识“，判断用户是否拥有某个“权限”';
CREATE TABLE IF NOT EXISTS "eva_role" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "code" VARCHAR(128) NOT NULL UNIQUE,
    "name" VARCHAR(128) NOT NULL,
    "description" TEXT
);
COMMENT ON TABLE "eva_role" IS '角色与一组权限绑定，用户可以属于多个角色。';
CREATE TABLE IF NOT EXISTS "eva_security_code" (
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "credential_id" BIGINT NOT NULL REFERENCES "eva_credential" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "eva_security_code" IS '验证码验证方式';
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "eva_identity_eva_role" (
    "eva_identity_id" BIGINT NOT NULL REFERENCES "eva_identity" ("id") ON DELETE CASCADE,
    "role_id" BIGINT NOT NULL REFERENCES "eva_role" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "eva_role_eva_permission" (
    "eva_role_id" BIGINT NOT NULL REFERENCES "eva_role" ("id") ON DELETE CASCADE,
    "permission_id" BIGINT NOT NULL REFERENCES "eva_permission" ("id") ON DELETE CASCADE
);

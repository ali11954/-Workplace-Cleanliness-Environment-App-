"""Add missing fields to Evaluation table

Revision ID: e38b97aff172
Revises:
Create Date: 2025-08-02 21:11:03.880877

"""
"""add missing fields to evaluation table"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'e38b97aff172'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # التحقق من وجود جدول قبل محاولة حذفه
    conn = op.get_bind()
    inspector = inspect(conn)

    if 'location_criterion' in inspector.get_table_names():
        op.drop_table('location_criterion')

    # يمكنك هنا إضافة الحقول الجديدة التي ترغب بها في جدول evaluation مثلاً:
    op.add_column('evaluation', sa.Column('new_column_name', sa.String(), nullable=True))

def downgrade():
    # استرجاع ما تم تغييره في upgrade
    op.add_column('location_criterion', sa.Column('id', sa.Integer(), primary_key=True))  # إن أردت استرجاع الجدول
    op.drop_column('evaluation', 'new_column_name')


    with op.batch_alter_table('criterion', schema=None) as batch_op:
        batch_op.alter_column('name',
            existing_type=sa.VARCHAR(length=150),
            type_=sa.String(length=255),
            existing_nullable=False)
        batch_op.alter_column('min_score',
            existing_type=sa.INTEGER(),
            type_=sa.Float(),
            existing_nullable=False)
        batch_op.alter_column('max_score',
            existing_type=sa.INTEGER(),
            type_=sa.Float(),
            existing_nullable=False)
        batch_op.alter_column('place_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.create_foreign_key('fk_criterion_place_id', 'place', ['place_id'], ['id'])

    with op.batch_alter_table('evaluation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('region_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('site_id', sa.Integer(), nullable=True))

        # حذف قيود قديمة (إن وُجدت)
        batch_op.drop_constraint('fk_evaluation_old_location_id', type_='foreignkey')  # استبدل بالاسم الفعلي إن وُجد

        # إضافة قيود بأسماء واضحة
        batch_op.create_foreign_key('fk_evaluation_site_id', 'site', ['site_id'], ['id'])
        batch_op.create_foreign_key('fk_evaluation_place_id', 'place', ['place_id'], ['id'])
        batch_op.create_foreign_key('fk_evaluation_region_id', 'location', ['region_id'], ['id'])
        batch_op.create_foreign_key('fk_evaluation_criterion_id', 'criterion', ['criterion_id'], ['id'])

        batch_op.drop_column('location_id')

    with op.batch_alter_table('evaluation_detail', schema=None) as batch_op:
        batch_op.alter_column('user_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.alter_column('score',
            existing_type=sa.INTEGER(),
            type_=sa.Float(),
            existing_nullable=False)
        batch_op.alter_column('timestamp',
            existing_type=sa.INTEGER(),
            type_=sa.DateTime(),
            existing_nullable=True)
        batch_op.create_foreign_key('fk_eval_detail_user_id', 'user', ['user_id'], ['id'])

    with op.batch_alter_table('site', schema=None) as batch_op:
        batch_op.alter_column('region_id',
            existing_type=sa.INTEGER(),
            nullable=False)
        batch_op.create_foreign_key('fk_site_region_id', 'location', ['region_id'], ['id'])

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('is_admin',
            existing_type=sa.INTEGER(),
            type_=sa.Boolean(),
            existing_nullable=True)

    with op.batch_alter_table('evaluation', schema=None) as batch_op:
        batch_op.add_column(sa.Column('location_id', sa.INTEGER(), nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key(None, 'location', ['location_id'], ['id'])
        batch_op.drop_column('site_id')
        batch_op.drop_column('region_id')

    with op.batch_alter_table('criterion', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('place_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.alter_column('max_score',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=False)
        batch_op.alter_column('min_score',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=False)
        batch_op.alter_column('name',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=150),
               existing_nullable=False)

    op.create_table('location_criterion',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('location_id', sa.INTEGER(), nullable=False),
    sa.Column('criterion_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['criterion_id'], ['criterion.id'], ),
    sa.ForeignKeyConstraint(['location_id'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###

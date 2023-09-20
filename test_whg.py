from src.whitehat import create_account, Registration

reg = Registration.find_by_id('64f0ef06366f5e8bd04bce75')

create_account(reg)
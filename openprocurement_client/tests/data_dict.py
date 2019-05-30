# -*- coding: utf-8 -
from openprocurement_client.compatibility_utils import munchify_factory


munchify = munchify_factory()


TEST_TENDER_KEYS = munchify({
    "tender_id": '823d50b3236247adad28a5a66f74db42',
    "empty_tender": 'f3849ade33534174b8402579152a5f41',
    "question_id": '615ff8be8eba4a81b300036d6bec991c',
    "lot_id": '563ef5d999f34d36a5a0e4e4d91d7be1',
    "bid_id": 'f7fc1212f9f140bba5c4e3cd4f2b62d9',
    "bid_document_id": "ff001412c60c4164a0f57101e4eaf8aa",
    "bid_qualification_document_id": "7519d21b32af432396acd6e2c9e18ee5",
    "bid_financial_document_id": "7519d21b32af432396acd6e2c9e18ee5",
    "bid_eligibility_document_id": "7519d21b32af432396acd6e2c9e18ee5",
    "award_id": '7054491a5e514699a56e44d32e23edf7',
    "qualification_id": "cec4b82d2708465291fb4af79f8a3e52",
    "document_id": '330822cbbd724671a1d2ff7c3a51dd52',
    "new_document_id": '7206763e862c4689a51dfcf821771c61',
    "error_id": '111a11a1111111aaa11111a1a1a111a1',
    "token": 'f6247c315d2744f1aa18c7c3de523bc3',
    "new_token": '4fa3e89efbaa46f0a1b86b911bec76e7'
})

TEST_TENDER_KEYS_LIMITED = munchify({
    "tender_id": '668c3156c8cb496fb28359909cde6e96',
    "cancellation_id": "0dd6f9e8cc4f4d1c9c404d842b56d0d7",
    "cancellation_document_id": "1afca9faaf2b4f9489ee264b136371c6",
    "document_id": "330822cbbd724671a1d2ff7c3a51dd52",
    "contract_id": "c65d3526cdc44f75b2457b4489970a7c",
    "complaint_id": "22b086222a7a4bc6a9cc8adeaa91a57f",
    "complaint_document_id": "129f4013b33a45b8bc70699a62a81499"
})

TEST_PLAN_KEYS = munchify({
    "plan_id": '34cebf0e7b474753854b0ef155b4a0f1',
    "error_id": 'xxx111'
})

TEST_CONTRACT_KEYS = munchify({
    "contract_id": '3c0bf3eed3fc4b189103e62b828c599d',
    "document_id": '9c8b66120d4c415cb334bbad33f94ba9',
    "new_document_id": 'newid678123456781234567812345678',
    "error_id": 'zzzxxx111',
    "contract_token": '0fc58c83963d42a692db4987df86640a',
    "change_id": '3ba8592459904c73bf05d7bc48e7083c',
    "patch_change_rationale": u'Друга і третя поставка має бути розфасована',
    "new_token": 'new0contract0token123412341234',
    "milestone_id": "7832794cb7474885a9e0536ce198ac88",
})

TEST_LOT_KEYS = munchify({
    "asset_id": '823d50b3236247adad28a5a66f74db42',
    "lot_id": '823d50b3236247adad28a5a66f74db42',
    "token": 'f6247c315d2744f1aa18c7c3de523bc3',
    "new_token": '4fa3e89efbaa46f0a1b86b911bec76e7'

})

TEST_ASSET_KEYS = munchify({
    "asset_id": '823d50b3236247adad28a5a66f74db42',
    "lot_id": '823d50b3236247adad28a5a66f74db42',
    "token": 'f6247c315d2744f1aa18c7c3de523bc3',
    "new_token": '4fa3e89efbaa46f0a1b86b911bec76e7'

})

TEST_TENDER_KEYS_AGREEMENT = munchify({
    "tender_id": 'c3f4116d38d34fe2b7d8de8aae8c0b32',
    "agreement_id": '9aa744f37d10468685a77be968bfe979',
    "amount": 2872000,
})

TEST_AGREEMENT_KEYS = munchify({
    "agreement_id": '362bc5f899664fa4a5f1ad957e39b88e',
    "change_id": 'd49a2fdeddd24194ab3e8e5c2265f6c0',
    "document_id": 'fdf7279ff77d4f7fb307e71a050c687d',
})

TEST_MONITORING_KEYS = munchify({
    "monitoring_id": 'f32f928d57d8485890b694cb2e02f864',
    "dialogue_id": '484e0eba91d348c9b372e7da7218a095',
    "description": 'The procurement requirements have been fixed and the changes are attached',
    "title": 'The procurement requirements have been fixed',
    "name": 'The State Audit Service of Ukraine',
    "roles": 'sas'
})

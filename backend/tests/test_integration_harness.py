from verify_domain_integration import test_database_name as make_name


def test_generated_database_names_fit_atlas_limit_and_are_distinct():
    names = {make_name() for _ in range(100)}
    assert len(names) == 100
    assert all(name.startswith('havosec_test_') and len(name.encode('utf-8')) <= 38 for name in names)

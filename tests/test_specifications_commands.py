from unittest.mock import MagicMock, patch

from igtools.specifications.commands import ReleaseCommand


def test_release_command_adds_previous_release_to_diff_to_when_confirmed():
    args = MagicMock(
        version="1.2.0",
        force=False,
        yes=False,
        directory="data",
        final=False,
        freeze=False,
        unfreeze=False,
        is_frozen=False
    )

    config = MagicMock(current="1.1.0", diff_to=["1.0.0"], directory="data")

    mock_release_manager = MagicMock()
    mock_processor = MagicMock()

    with patch("igtools.specifications.commands.cli.confirm_action", side_effect=[True, True, False]) as mock_confirm, \
         patch("igtools.specifications.commands.ReleaseManager", return_value=mock_release_manager), \
         patch("igtools.specifications.commands.Processor", return_value=mock_processor):
        cmd = ReleaseCommand()
        cmd.run(config=config, args=args)

    assert config.diff_to == ["1.0.0", "1.1.0"]
    mock_release_manager.create.assert_called_once_with(version="1.2.0", force=False)
    assert mock_confirm.call_count == 3


def test_release_command_skips_diff_to_prompt_if_previous_release_already_added():
    args = MagicMock(
        version="1.2.0",
        force=False,
        yes=False,
        directory="data",
        final=False,
        freeze=False,
        unfreeze=False,
        is_frozen=False
    )

    config = MagicMock(current="1.1.0", diff_to=["1.0.0", "1.1.0"], directory="data")

    mock_release_manager = MagicMock()
    mock_release_manager.check_new_version.return_value = None
    mock_release_manager.create.return_value = None

    mock_processor = MagicMock()
    mock_processor.process.return_value = None
    mock_processor.reset_all_meta_tags.return_value = None

    with patch("igtools.specifications.commands.cli.confirm_action", side_effect=[True, False]) as mock_confirm, \
         patch("igtools.specifications.commands.ReleaseManager", return_value=mock_release_manager), \
         patch("igtools.specifications.commands.Processor", return_value=mock_processor):
        cmd = ReleaseCommand()
        cmd.run(config=config, args=args)

    assert config.diff_to == ["1.0.0", "1.1.0"]
    mock_release_manager.create.assert_called_once_with(version="1.2.0", force=False)
    assert mock_confirm.call_count == 2


def test_release_command_removes_selected_releases_from_diff_to():
    args = MagicMock(
        version="1.2.0",
        force=False,
        yes=False,
        directory="data",
        final=False,
        freeze=False,
        unfreeze=False,
        is_frozen=False
    )

    config = MagicMock(current="1.1.0", diff_to=["1.0.0", "1.1.0"], directory="data")

    mock_release_manager = MagicMock()
    mock_release_manager.is_current_release_frozen.return_value = False
    mock_release_manager.check_new_version.return_value = None
    mock_release_manager.create.return_value = None

    mock_processor = MagicMock()
    mock_processor.process.return_value = None
    mock_processor.reset_all_meta_tags.return_value = None

    with patch("igtools.specifications.commands.cli.confirm_action", side_effect=[True, True]) as mock_confirm, \
         patch("builtins.input", return_value="1.0.0"), \
         patch("igtools.specifications.commands.ReleaseManager", return_value=mock_release_manager), \
         patch("igtools.specifications.commands.Processor", return_value=mock_processor):
        cmd = ReleaseCommand()
        cmd.run(config=config, args=args)

    assert config.diff_to == ["1.1.0"]
    mock_release_manager.create.assert_called_once_with(version="1.2.0", force=False)
    assert mock_confirm.call_count == 2


def test_release_command_keeps_diff_to_when_remove_prompt_declined():
    args = MagicMock(
        version="1.2.0",
        force=False,
        yes=False,
        directory="data",
        final=False,
        freeze=False,
        unfreeze=False,
        is_frozen=False
    )

    config = MagicMock(current="1.1.0", diff_to=["1.0.0", "1.1.0"], directory="data")

    mock_release_manager = MagicMock()
    mock_release_manager.is_current_release_frozen.return_value = False
    mock_release_manager.check_new_version.return_value = None
    mock_release_manager.create.return_value = None

    mock_processor = MagicMock()
    mock_processor.process.return_value = None
    mock_processor.reset_all_meta_tags.return_value = None

    with patch("igtools.specifications.commands.cli.confirm_action", side_effect=[True, False]) as mock_confirm, \
         patch("igtools.specifications.commands.ReleaseManager", return_value=mock_release_manager), \
         patch("igtools.specifications.commands.Processor", return_value=mock_processor):
        cmd = ReleaseCommand()
        cmd.run(config=config, args=args)

    assert config.diff_to == ["1.0.0", "1.1.0"]
    mock_release_manager.create.assert_called_once_with(version="1.2.0", force=False)
    assert mock_confirm.call_count == 2

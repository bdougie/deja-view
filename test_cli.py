#!/usr/bin/env python3
import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock
from cli import cli, format_similarity_score


class TestFormatSimilarityScore:
    def test_high_score_green(self):
        assert "[green]85.00%[/green]" in format_similarity_score(0.85)
        assert "[green]80.00%[/green]" in format_similarity_score(0.80)
    
    def test_medium_score_yellow(self):
        assert "[yellow]70.00%[/yellow]" in format_similarity_score(0.70)
        assert "[yellow]60.00%[/yellow]" in format_similarity_score(0.60)
    
    def test_low_score_red(self):
        assert "[red]50.00%[/red]" in format_similarity_score(0.50)
        assert "[red]30.00%[/red]" in format_similarity_score(0.30)


class TestCLICommands:
    def setup_method(self):
        self.runner = CliRunner()
        self.mock_service = Mock()
    
    @patch('cli.SimilarityService')
    def test_index_command_success(self, mock_service_class):
        mock_service_class.return_value = self.mock_service
        self.mock_service.index_repository.return_value = {
            'indexed': 50,
            'issues': 40,
            'discussions': 10,
            'repository': 'owner/repo'
        }
        
        result = self.runner.invoke(cli, ['index', 'owner/repo', '--max-issues', '50', '--include-discussions'])
        
        assert result.exit_code == 0
        assert "Successfully indexed" in result.output
        assert "50" in result.output
        self.mock_service.index_repository.assert_called_once_with('owner', 'repo', 50, True)
    
    @patch('cli.SimilarityService')
    def test_index_command_invalid_repo_format(self, mock_service_class):
        result = self.runner.invoke(cli, ['index', 'invalid-format'])
        
        assert result.exit_code == 1
        assert "Repository must be in format 'owner/repo'" in result.output
        mock_service_class.assert_not_called()
    
    @patch('cli.SimilarityService')
    def test_find_command_success(self, mock_service_class):
        mock_service_class.return_value = self.mock_service
        self.mock_service.find_similar_issues.return_value = [
            {
                'number': 123,
                'title': 'Test Issue',
                'similarity': 0.85,
                'state': 'open',
                'url': 'https://github.com/owner/repo/issues/123',
                'is_pull_request': False,
                'is_discussion': False
            }
        ]
        
        result = self.runner.invoke(cli, ['find', 'https://github.com/owner/repo/issues/456'])
        
        assert result.exit_code == 0
        assert "Test Issue" in result.output
        assert "85" in result.output
        self.mock_service.find_similar_issues.assert_called_once_with('owner', 'repo', 456, 10, 0.0)
    
    @patch('cli.SimilarityService')
    def test_find_command_invalid_url(self, mock_service_class):
        result = self.runner.invoke(cli, ['find', 'not-a-valid-url'])
        
        assert result.exit_code == 1
        assert "Invalid issue/PR URL" in result.output
        mock_service_class.assert_not_called()
    
    @patch('cli.SimilarityService')
    def test_find_command_no_results(self, mock_service_class):
        mock_service_class.return_value = self.mock_service
        self.mock_service.find_similar_issues.return_value = []
        
        result = self.runner.invoke(cli, ['find', 'https://github.com/owner/repo/issues/456'])
        
        assert result.exit_code == 0
        assert "No similar issues found" in result.output
    
    @patch('cli.SimilarityService')
    def test_stats_command(self, mock_service_class):
        mock_service_class.return_value = self.mock_service
        self.mock_service.get_stats.return_value = {
            'total_issues': 100,
            'repositories': ['owner/repo1', 'owner/repo2']
        }
        
        result = self.runner.invoke(cli, ['stats'])
        
        assert result.exit_code == 0
        assert "Total Issues:" in result.output
        assert "100" in result.output
        assert "owner/repo1" in result.output
        assert "owner/repo2" in result.output
    
    @patch('cli.SimilarityService')
    def test_clear_command_confirmed(self, mock_service_class):
        mock_service_class.return_value = self.mock_service
        self.mock_service.clear_all.return_value = {'message': 'All issues cleared successfully'}
        
        result = self.runner.invoke(cli, ['clear'], input='y\n')
        
        assert result.exit_code == 0
        assert "All issues cleared successfully" in result.output
        self.mock_service.clear_all.assert_called_once()
    
    @patch('cli.SimilarityService')
    def test_clear_command_cancelled(self, mock_service_class):
        result = self.runner.invoke(cli, ['clear'], input='n\n')
        
        assert result.exit_code == 1
        mock_service_class.assert_not_called()
    
    @patch('cli.SimilarityService')
    def test_quick_command_with_index(self, mock_service_class):
        mock_service_class.return_value = self.mock_service
        self.mock_service.index_repository.return_value = {'indexed': 100}
        self.mock_service.find_similar_issues.return_value = [
            {
                'number': 123,
                'title': 'Test Issue',
                'similarity': 0.75,
                'state': 'open'
            }
        ]
        
        result = self.runner.invoke(cli, ['quick', 'owner/repo', '456', '--index-first'])
        
        assert result.exit_code == 0
        assert "Indexed 100 issues" in result.output
        assert "Test Issue" in result.output
        self.mock_service.index_repository.assert_called_once()
        self.mock_service.find_similar_issues.assert_called_once()
    
    @patch('cli.SimilarityService')
    def test_suggest_discussions_dry_run(self, mock_service_class):
        mock_service_class.return_value = self.mock_service
        self.mock_service.suggest_discussions.return_value = {
            'suggestions': [
                {
                    'number': 123,
                    'title': 'How to use feature X?',
                    'score': 0.75,
                    'state': 'open',
                    'reasons': ['Contains question pattern', 'Has question label']
                }
            ],
            'total_analyzed': 50
        }
        
        result = self.runner.invoke(cli, ['suggest-discussions', 'owner/repo'])
        
        assert result.exit_code == 0
        assert "DRY RUN MODE" in result.output
        # Check for title content (may be wrapped in table)
        assert "How to use feature" in result.output
        assert "0.75" in result.output
        self.mock_service.suggest_discussions.assert_called_once_with('owner', 'repo', 0.3, 20, True)
    
    @patch('cli.SimilarityService')
    def test_suggest_discussions_execute(self, mock_service_class):
        mock_service_class.return_value = self.mock_service
        self.mock_service.suggest_discussions.return_value = {
            'suggestions': [],
            'total_analyzed': 10
        }
        
        result = self.runner.invoke(cli, ['suggest-discussions', 'owner/repo', '--execute'])
        
        assert result.exit_code == 0
        assert "No issues found that should be discussions" in result.output
        self.mock_service.suggest_discussions.assert_called_once_with('owner', 'repo', 0.3, 20, False)
    
    @patch('cli.SimilarityService')
    def test_error_handling(self, mock_service_class):
        mock_service_class.return_value = self.mock_service
        self.mock_service.index_repository.side_effect = Exception("API Error")
        
        result = self.runner.invoke(cli, ['index', 'owner/repo'])
        
        assert result.exit_code == 1
        assert "Error: API Error" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])